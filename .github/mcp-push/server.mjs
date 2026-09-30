import { timingSafeEqual } from 'node:crypto';
import { createServer } from 'node:http';
import { createMcpHandler, McpServer } from '@modelcontextprotocol/server';
import { toNodeHandler } from '@modelcontextprotocol/node';
import * as push from 'push-all-in-one';
import * as z from 'zod/v4';

const prefix = 'MCP_PUSH_';
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

function readConfig(channel) {
    const config = {};
    const missing = [];
    for (const [key, meta] of Object.entries(push.PushAllInOne[channel].configSchema)) {
        let value = process.env[prefix + key] ?? meta.default;
        if (value === undefined || value === '' || (meta.required && value === 0)) {
            if (meta.required) missing.push(prefix + key);
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

// Provider errors may contain request URLs. Never return configured credentials.
function redact(value) {
    const secrets = Object.entries(process.env)
        .filter(([key, value]) => key.startsWith(prefix) && /(?:TOKEN|SECRET|KEY|PASS|AUTH|WEBHOOK|TOPIC|PROXY|PROXY_URL)$/.test(key) && value)
        .map(([, value]) => value)
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

function result(value, isError = false) {
    return { content: [{ type: 'text', text: redact(value) }], isError };
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

function buildServer() {
    const server = new McpServer({ name: 'mcp-push', version: '1.0.0' });
    server.registerTool('list_push_channels', {
        description: 'List push channels, missing server configuration and channel-specific send options. Credential values are never returned.',
        inputSchema: z.object({ channel: z.enum(channels).optional() }),
        annotations: { readOnlyHint: true, openWorldHint: false },
    }, async ({ channel }) => result((channel ? [channel] : channels).map(name => {
        try {
            const { missing } = readConfig(name);
            return { channel: name, configured: missing.length === 0, missing, options: push.PushAllInOne[name].optionSchema };
        } catch (error) {
            return { channel: name, configured: false, error: error.message };
        }
    })));
    server.registerTool('send_push', {
        description: 'Send a notification using a server-configured channel. Call list_push_channels for available channels and options. This sends a real external message; do not retry automatically after a timeout because delivery may already have occurred. Inspect the provider response for acceptance; HTTP 200 alone does not confirm delivery.',
        inputSchema: z.object({
            channel: z.enum(channels),
            title: z.string().min(1).max(4096),
            body: z.string().max(131072).default(''),
            options: z.record(z.string(), z.unknown()).default({}),
        }),
        annotations: { readOnlyHint: false, destructiveHint: false, idempotentHint: false, openWorldHint: true },
    }, async ({ channel, title, body, options }) => {
        let provider;
        try {
            const { config, missing } = readConfig(channel);
            if (missing.length) return result({ error: 'Channel is not configured', missing }, true);
            provider = new push.PushAllInOne[channel](config);
            if (channel === 'CustomEmail') {
                options = { ...options, disableFileAccess: true, disableUrlAccess: true };
            }
            const response = await provider.send(title, body, options);
            return result({ channel, status: response.status, data: response.data }, pushFailed(channel, response));
        } catch (error) {
            return result({ channel, error: error.message || 'Push failed' }, true);
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
