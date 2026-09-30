import { timingSafeEqual } from 'node:crypto';
import { createServer } from 'node:http';
import { createMcpHandler, McpServer } from '@modelcontextprotocol/server';
import { toNodeHandler } from '@modelcontextprotocol/node';
import * as push from 'push-all-in-one';
import * as z from 'zod/v4';

const prefix = 'MCP_PUSH_';
const channelHeaderName = 'X-CHANNEL';
const token = process.env.MCP_PUSH_TOKEN;
if (!token || token.length < 32 || /\s/.test(token)) {
    throw new Error('MCP_PUSH_TOKEN must contain at least 32 characters without whitespace');
}
const expectedAuthorization = Buffer.from(`Bearer ${token}`);
const allowedOrigins = new Set((process.env.MCP_PUSH_ALLOWED_ORIGINS || '').split(',').map(s => s.trim()).filter(Boolean));
const channels = Object.keys(push.PushAllInOne);

// Proxy variables follow the upstream library's conventions.
for (const key of ['HTTP_PROXY', 'HTTPS_PROXY', 'SOCKS_PROXY', 'NO_PROXY']) {
    if (process.env[prefix + key] !== undefined) process.env[key] = process.env[prefix + key];
}

function configHeaderName(key) {
    return `X-${key.replaceAll('_', '-')}`;
}

function parameterHeaderName(key) {
    const normalized = key.replace(/([a-z0-9])([A-Z])/g, '$1-$2').replaceAll('_', '-').toUpperCase();
    return `X-ARG-${normalized}`;
}

const channelConfigHeaders = new Set(channels.flatMap(channel =>
    Object.keys(push.PushAllInOne[channel].configSchema).map(key => configHeaderName(key).toLowerCase()),
));

function readConfig(channel, request) {
    const config = {};
    const missing = [];
    for (const [key, meta] of Object.entries(push.PushAllInOne[channel].configSchema)) {
        let value = request?.headers.get(configHeaderName(key)) ?? meta.default;
        if (value === undefined || value === '' || (meta.required && value === 0)) {
            if (meta.required) missing.push(configHeaderName(key));
            continue;
        }
        if (meta.type === 'number') {
            value = Number(value);
            if (!Number.isFinite(value)) throw new Error(`${prefix + key} must be a number`);
        }
        if (meta.type === 'select' && !meta.options.some(option => option.value === value)) {
            throw new Error(`${prefix + key} has an unsupported value`);
        }
        config[key] = value;
    }
    return { config, missing };
}

function requestSecrets(request) {
    return [...(request?.headers ?? [])]
        .filter(([name]) => channelConfigHeaders.has(name))
        .map(([, value]) => value)
        .filter(Boolean);
}

// Provider errors may contain request URLs. Never return configured credentials.
function redact(value, extraSecrets = []) {
    const secrets = Object.entries(process.env)
        .filter(([key, value]) => key.startsWith(prefix) && /(?:TOKEN|SECRET|KEY|PASS|AUTH|WEBHOOK|TOPIC|PROXY|PROXY_URL)$/.test(key) && value)
        .map(([, value]) => value)
        .concat(extraSecrets)
        .sort((a, b) => b.length - a.length);
    return JSON.stringify(value, (_, item) => {
        if (typeof item !== 'string') return item;
        for (const secret of secrets) {
            for (const variant of [secret, encodeURIComponent(secret)]) {
                item = item.replaceAll(variant, '[redacted]');
            }
        }
        return item;
    });
}

function result(value, isError = false, secrets = []) {
    return { content: [{ type: 'text', text: redact(value, secrets) }], isError };
}

function optionArraySchema(channel, key) {
    if (channel === 'ServerChanV3' && key === 'tags') return z.array(z.string());
    if (channel === 'WxPusher' && key === 'topicIds') return z.array(z.number());
    if (channel === 'WxPusher' && key === 'uids') return z.array(z.string());
    throw new Error(`No item schema is defined for array option ${channel}.${key}`);
}

function optionObjectSchema(channel, key) {
    if (channel === 'Dingtalk') {
        const optionalString = z.string().optional();
        const button = z.object({
            title: z.string(),
            actionURL: z.string(),
        }).strict();
        const link = z.object({
            title: optionalString,
            text: optionalString,
            picUrl: optionalString,
            messageUrl: optionalString,
        }).strict();
        const schemas = {
            text: z.object({ content: optionalString }).strict(),
            markdown: z.object({ title: optionalString, text: optionalString }).strict(),
            link,
            actionCard: z.object({
                title: optionalString,
                text: optionalString,
                btnOrientation: z.enum(['0', '1']).optional(),
                singleTitle: optionalString,
                singleURL: optionalString,
                btns: z.array(button).optional(),
            }).strict(),
            feedCard: z.object({
                links: z.array(z.object({
                    title: z.string(),
                    messageURL: z.string(),
                    picURL: z.string(),
                }).strict()).optional(),
            }).strict(),
        };
        if (schemas[key]) return schemas[key];
    }
    if (channel === 'Ntfy' && key === 'file') {
        return z.object({
            name: z.string().min(1).describe('Attachment filename.'),
            size: z.number().int().nonnegative().describe('Attachment payload size in bytes; the payload is supplied in body.'),
        }).strict();
    }
    throw new Error(`No field schema is defined for object option ${channel}.${key}`);
}

function optionFieldSchema(channel, key, meta) {
    let schema;
    switch (meta.type) {
        case 'string':
            schema = z.string();
            break;
        case 'number':
            schema = z.number();
            break;
        case 'boolean':
            schema = z.boolean();
            break;
        case 'select': {
            const values = (meta.options || []).map(option => option.value);
            if (!values.length) throw new Error(`Select option ${key} has no allowed values`);
            schema = values.every(value => typeof value === 'string')
                ? z.enum(values)
                : values.length === 1
                    ? z.literal(values[0])
                    : z.union(values.map(value => z.literal(value)));
            break;
        }
        case 'array':
            schema = optionArraySchema(channel, key);
            break;
        case 'object':
            schema = optionObjectSchema(channel, key);
            break;
        default:
            throw new Error(`Unsupported option type for ${key}: ${meta.type}`);
    }
    // Structural option defaults like Dingtalk's empty message objects overwrite
    // the provider's title/body-generated payload when spread into its request.
    if (meta.default !== undefined && meta.type !== 'object') schema = schema.default(meta.default);
    else if (!meta.required) schema = schema.optional();
    const description = [meta.title, meta.description].filter(Boolean).join(': ');
    return description ? schema.describe(description) : schema.describe(key);
}

function oneBotInputSchema(shape, optionSchema, request) {
    const hasMessageTypeHeader = hasParameterHeader(request, 'message_type');
    const messageTypeHeader = request?.headers.get(parameterHeaderName('message_type'));
    const messageTypeDescription = [optionSchema.message_type.title, optionSchema.message_type.description]
        .filter(Boolean).join(': ');

    const makeShape = (messageType, includeMessageType) => {
        const result = { ...shape };
        if (includeMessageType) {
            result.message_type = messageType === 'private'
                ? z.literal('private').default('private')
                : z.literal('group');
            if (messageTypeDescription) result.message_type = result.message_type.describe(messageTypeDescription);
        }
        const requiredRecipient = messageType === 'private' ? 'user_id' : 'group_id';
        const otherRecipient = messageType === 'private' ? 'group_id' : 'user_id';
        for (const [key, required] of [[requiredRecipient, true], [otherRecipient, false]]) {
            if (hasParameterHeader(request, key)) continue;
            result[key] = optionFieldSchema('OneBot', key, {
                ...optionSchema[key],
                default: undefined,
                required,
            });
        }
        return z.object(result).strict();
    };

    if (hasMessageTypeHeader) {
        if (messageTypeHeader === 'private' || messageTypeHeader === 'group') {
            return makeShape(messageTypeHeader, false);
        }
        // Keep tools/list available for an invalid fixed header; tools/call will
        // report the invalid enum value through parseParameterHeader.
        const result = { ...shape };
        for (const key of ['user_id', 'group_id']) {
            if (hasParameterHeader(request, key)) continue;
            result[key] = optionFieldSchema('OneBot', key, {
                ...optionSchema[key],
                default: undefined,
                required: false,
            }).describe(`${optionSchema[key].description} (required for the matching message_type)`);
        }
        return z.object(result).strict();
    }

    return z.union([
        makeShape('private', true),
        makeShape('group', true),
    ]);
}

function hasParameterHeader(request, key) {
    const value = request?.headers.get(parameterHeaderName(key));
    return value !== null && value !== undefined && value !== '';
}

function decodeUtf8HeaderString(value) {
    if (!value.includes('%')) return value;
    try {
        const decoded = decodeURIComponent(value);
        return /[^\x00-\x7f]/.test(decoded) ? decoded : value;
    } catch {
        return value;
    }
}

function parseParameterHeader(channel, key, meta, value) {
    const headerName = parameterHeaderName(key);
    let parsed;
    switch (meta.type) {
        case 'string':
            parsed = decodeUtf8HeaderString(value);
            break;
        case 'number': {
            const number = Number(value);
            if (!Number.isFinite(number)) throw new Error(`${headerName} must be a number`);
            parsed = number;
            break;
        }
        case 'boolean':
            if (value.toLowerCase() === 'true') parsed = true;
            else if (value.toLowerCase() === 'false') parsed = false;
            else throw new Error(`${headerName} must be true or false`);
            break;
        case 'select': {
            const selected = (meta.options || []).find(option => String(option.value) === value);
            if (!selected) throw new Error(`${headerName} has an unsupported value`);
            parsed = selected.value;
            break;
        }
        case 'array':
        case 'object': {
            try {
                const jsonValue = /^%(?:7B|5B)/i.test(value) ? decodeURIComponent(value) : value;
                parsed = JSON.parse(jsonValue);
            } catch {
                throw new Error(`${headerName} must contain valid JSON`);
            }
            if (meta.type === 'array' && !Array.isArray(parsed)) throw new Error(`${headerName} must contain a JSON array`);
            if (meta.type === 'object' && (parsed === null || typeof parsed !== 'object' || Array.isArray(parsed))) {
                throw new Error(`${headerName} must contain a JSON object`);
            }
            break;
        }
        default:
            throw new Error(`Unsupported header parameter type for ${key}: ${meta.type}`);
    }

    const commonSchema = commonInputFields()[key];
    const schema = commonSchema || optionFieldSchema(channel, key, { ...meta, default: undefined, required: true });
    try {
        return schema.parse(parsed);
    } catch {
        throw new Error(`${headerName} has an invalid value`);
    }
}

function getParameterValue(channel, key, meta, args, request) {
    const value = request?.headers.get(parameterHeaderName(key));
    if (value !== null && value !== undefined && value !== '') return parseParameterHeader(channel, key, meta, value);
    return args[key];
}

function commonInputFields() {
    return {
        title: z.string().min(1).max(4096).describe('Notification title.'),
        body: z.string().max(131072).default('').describe('Notification body; defaults to an empty string.'),
    };
}

function channelInputSchema(channel, request) {
    const optionSchema = push.PushAllInOne[channel].optionSchema || {};
    const commonFields = commonInputFields();
    const shape = {};
    for (const [key, schema] of Object.entries(commonFields)) {
        if (!hasParameterHeader(request, key)) shape[key] = schema;
    }
    for (const [key, meta] of Object.entries(optionSchema)) {
        // Ntfy declares these same fields as channel options; the common arguments serve both roles.
        if (Object.hasOwn(commonFields, key) || hasParameterHeader(request, key)) continue;
        if (channel === 'OneBot' && ['message_type', 'user_id', 'group_id'].includes(key)) continue;
        shape[key] = optionFieldSchema(channel, key, meta);
    }
    if (channel === 'OneBot') return oneBotInputSchema(shape, optionSchema, request);
    return z.object(shape).strict();
}

function pushFailed(channel, response) {
    if (response.status < 200 || response.status >= 300) return true;
    const data = response.data;
    if (!data || typeof data !== 'object') return false;
    if (typeof data.success === 'boolean') return !data.success;
    if (typeof data.ok === 'boolean') return !data.ok;
    for (const key of ['errcode', 'retcode', 'ret']) {
        if (typeof data[key] === 'number' && data[key] !== 0) return true;
    }
    if (typeof data.code === 'number') {
        const successCode = { PushPlus: 200, XiZhi: 200, WxPusher: 1000 }[channel] ?? 0;
        return data.code !== successCode;
    }
    return false;
}

function buildServer({ requestInfo } = {}) {
    const selectedChannel = requestInfo?.headers.get(channelHeaderName);
    const channelSelected = channels.includes(selectedChannel);
    const inputSchema = channelSelected
        ? channelInputSchema(selectedChannel, requestInfo)
        : z.object(Object.fromEntries(Object.entries(commonInputFields()).filter(([key]) => !hasParameterHeader(requestInfo, key)))).strict();
    const server = new McpServer({ name: 'mcp-push', version: '1.0.0' });
    server.registerTool('send_push', {
        description: channelSelected
            ? `Send a ${selectedChannel} notification. Channel-specific arguments are listed with their types, descriptions, allowed values and required status. Parameters supplied through matching X-ARG-<argument-name> headers are read per request and omitted from the tool schema. Channel credentials use channel-specific X-* request headers. This sends a real external message; do not retry automatically after a timeout because delivery may already have occurred. Inspect the provider response for acceptance; HTTP 200 alone does not confirm delivery.`
            : `Send a notification using the channel selected by the ${channelHeaderName} HTTP header. Set that header in the MCP client configuration before listing tools to expose the channel-specific arguments. Parameters supplied through matching X-ARG-<argument-name> headers are read per request and omitted from the tool schema. This sends a real external message; do not retry automatically after a timeout because delivery may already have occurred. Inspect the provider response for acceptance; HTTP 200 alone does not confirm delivery.`,
        inputSchema,
        annotations: { readOnlyHint: false, destructiveHint: false, idempotentHint: false, openWorldHint: true },
    }, async (args, context) => {
        let provider;
        const request = context.http?.req;
        const secrets = requestSecrets(request);
        const channel = request?.headers.get(channelHeaderName);
        if (!channels.includes(channel)) {
            return result({ error: `Set ${channelHeaderName} to a supported channel`, supportedChannels: channels }, true, secrets);
        }
        try {
            const title = getParameterValue(channel, 'title', { type: 'string' }, args, request);
            const body = getParameterValue(channel, 'body', { type: 'string' }, args, request) ?? '';
            const optionSchema = push.PushAllInOne[channel].optionSchema || {};
            let options = {};
            for (const [key, meta] of Object.entries(optionSchema)) {
                const value = getParameterValue(channel, key, meta, args, request);
                if (value !== undefined) options[key] = value;
            }
            const { config, missing } = readConfig(channel, request);
            if (missing.length) return result({ error: 'Channel is not configured', missing }, true, secrets);
            provider = new push.PushAllInOne[channel](config);
            if (channel === 'CustomEmail') {
                options = { ...options, disableFileAccess: true, disableUrlAccess: true };
            }
            const response = await provider.send(title, body, options);
            return result({ channel, status: response.status, data: response.data }, pushFailed(channel, response), secrets);
        } catch (error) {
            return result({ channel, error: error.message || 'Push failed' }, true, secrets);
        } finally {
            provider?.[Symbol.dispose]?.();
        }
    });
    return server;
}

const handler = createMcpHandler(buildServer, { responseMode: 'json', maxRequestBodySize: 262144 });
const nodeHandler = toNodeHandler(handler, { maxRequestBodySize: 262144 });
const http = createServer(async (req, res) => {
    const path = req.url?.split('?')[0];
    if (path === '/health' && req.method === 'GET') {
        res.writeHead(200, { 'Content-Type': 'application/json' }).end('{"status":"ok"}');
        return;
    }
    if (path !== '/mcp') {
        res.writeHead(404).end();
        return;
    }
    const authorization = Buffer.from(req.headers.authorization || '');
    if (authorization.length !== expectedAuthorization.length || !timingSafeEqual(authorization, expectedAuthorization)) {
        res.writeHead(401, { 'WWW-Authenticate': 'Bearer realm="mcp-push"' }).end('Unauthorized');
        return;
    }
    if (req.headers.origin && !allowedOrigins.has(req.headers.origin)) {
        res.writeHead(403).end('Origin is not allowed');
        return;
    }
    try {
        await nodeHandler(req, res);
    } catch {
        if (!res.headersSent) res.writeHead(500).end('MCP request failed');
        else res.end();
    }
});
http.listen(Number(process.env.PORT || 8931), '0.0.0.0', () => console.error('Push MCP is listening on /mcp'));

for (const signal of ['SIGINT', 'SIGTERM']) {
    process.once(signal, () => {
        http.close(async () => {
            await handler.close();
            process.exit(0);
        });
        setTimeout(() => process.exit(0), 10000).unref();
    });
}
