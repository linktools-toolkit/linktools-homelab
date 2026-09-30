// Uses only a loopback ntfy fixture. No real notification is sent.
import assert from 'node:assert/strict';
import { createServer } from 'node:http';
import { once } from 'node:events';
import * as push from 'push-all-in-one';

const base = process.env.MCP_PUSH_TEST_URL || 'http://127.0.0.1:8931';
const token = process.env.MCP_PUSH_TOKEN;
const ntfyAuth = 'fixture-ntfy-header-secret';
const ntfyHeaders = {
    'X-CHANNEL': 'Ntfy',
    'X-Ntfy-Url': 'http://127.0.0.1:18932',
    'X-Ntfy-Topic': 'smoke-topic',
    'X-Ntfy-Auth': ntfyAuth,
    'X-PRIORITY': '5',
    'X-MARKDOWN': 'true',
    'X-BODY': encodeURIComponent('你好'),
};
assert.ok(token);
let nextId = 0;
let deliveries = 0;
const fixture = createServer(async (req, res) => {
    let body = '';
    for await (const chunk of req) body += chunk;
    assert.equal(req.url, '/smoke-topic');
    assert.equal(req.headers.authorization, ntfyAuth);
    assert.equal(req.headers['x-priority'], '5');
    assert.equal(req.headers['x-markdown'], 'true');
    assert.equal(body, '你好');
    deliveries++;
    const data = deliveries > 2
        ? { errcode: 400, errmsg: `fixture rejection ${ntfyAuth}` }
        : { id: 'fixture-message', event: 'message' };
    res.writeHead(200, { 'Content-Type': 'application/json' }).end(JSON.stringify(data));
});
fixture.listen(18932, '127.0.0.1');
await once(fixture, 'listening');

async function rpc(method, params = {}, headers = ntfyHeaders) {
    const response = await fetch(`${base}/mcp`, {
        method: 'POST',
        headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json',
            Accept: 'application/json, text/event-stream',
            ...headers,
        },
        body: JSON.stringify({ jsonrpc: '2.0', id: ++nextId, method, params }),
        signal: AbortSignal.timeout(10000),
    });
    const text = await response.text();
    assert.equal(response.status, 200, text);
    const data = text.startsWith('event:') || text.startsWith('data:')
        ? JSON.parse(text.split('\n').find(line => line.startsWith('data:')).slice(5))
        : JSON.parse(text);
    assert.equal(data.error, undefined, text);
    return data.result;
}

try {
    assert.equal((await fetch(`${base}/health`)).status, 200);
    assert.equal((await fetch(`${base}/mcp`)).status, 401);
    assert.equal((await fetch(`${base}/mcp`, { headers: { Authorization: 'Bearer wrong' } })).status, 401);
    assert.equal((await fetch(`${base}/mcp`, { headers: { Authorization: `Bearer ${token}`, Origin: 'https://untrusted.invalid' } })).status, 403);
    const init = await rpc('initialize', {
        protocolVersion: '2025-11-25', capabilities: {}, clientInfo: { name: 'smoke', version: '1.0.0' },
    });
    assert.equal(init.serverInfo.name, 'mcp-push');
    const tools = await rpc('tools/list');
    assert.deepEqual(tools.tools.map(tool => tool.name), ['send_push']);
    const ntfyInput = tools.tools[0].inputSchema;
    assert.equal(ntfyInput.additionalProperties, false);
    assert.equal(Object.hasOwn(ntfyInput.properties, 'priority'), false);
    assert.equal(Object.hasOwn(ntfyInput.properties, 'markdown'), false);
    assert.equal(Object.hasOwn(ntfyInput.properties, 'body'), false);
    assert.equal(ntfyInput.properties.tags.type, 'string');

    const feishuTools = await rpc('tools/list', {}, { 'X-CHANNEL': 'Feishu' });
    const feishuInput = feishuTools.tools[0].inputSchema;
    assert.deepEqual(Object.keys(feishuInput.properties).sort(), ['body', 'content', 'msg_type', 'receive_id', 'receive_id_type', 'title', 'uuid']);
    assert.deepEqual(feishuInput.required.sort(), ['msg_type', 'receive_id', 'receive_id_type', 'title']);
    assert.deepEqual(feishuInput.properties.receive_id_type.enum, ['open_id', 'union_id', 'user_id', 'email', 'chat_id']);
    assert.deepEqual(feishuInput.properties.msg_type.enum, ['text', 'post', 'image', 'file', 'audio', 'media', 'sticker', 'interactive', 'share_chat', 'share_user', 'system']);
    assert.equal(feishuInput.additionalProperties, false);

    const fixedFeishuHeaders = {
        'X-CHANNEL': 'Feishu',
        'X-TITLE': 'fixed title',
        'X-BODY': 'fixed body',
        'X-RECEIVE-ID-TYPE': 'chat_id',
        'X-RECEIVE-ID': 'oc_smoke',
        'X-MSG-TYPE': 'text',
    };
    const fixedFeishuTools = await rpc('tools/list', {}, fixedFeishuHeaders);
    const fixedFeishuInput = fixedFeishuTools.tools[0].inputSchema;
    assert.deepEqual(Object.keys(fixedFeishuInput.properties).sort(), ['content', 'uuid']);
    const fixedFeishuCall = await rpc('tools/call', { name: 'send_push', arguments: {} }, fixedFeishuHeaders);
    assert.equal(fixedFeishuCall.isError, true);
    assert.ok(JSON.parse(fixedFeishuCall.content[0].text).missing.includes('X-FEISHU-APP-ID'));

    const objectHeaderCall = await rpc('tools/call', {
        name: 'send_push', arguments: { title: 'Dingtalk object header' },
    }, { 'X-CHANNEL': 'Dingtalk', 'X-MARKDOWN': '{"title":"title","text":"body"}' });
    assert.equal(objectHeaderCall.isError, true);
    assert.ok(JSON.parse(objectHeaderCall.content[0].text).missing.includes('X-DINGTALK-ACCESS-TOKEN'));

    const arrayHeaderCall = await rpc('tools/call', {
        name: 'send_push', arguments: { title: 'WxPusher array header' },
    }, {
        'X-CHANNEL': 'WxPusher',
        'X-TOPIC-IDS': '[123]',
        'X-UIDS': '["uid-smoke"]',
    });
    assert.equal(arrayHeaderCall.isError, true);
    assert.ok(JSON.parse(arrayHeaderCall.content[0].text).missing.includes('X-WX-PUSHER-APP-TOKEN'));

    const wechatAppTools = await rpc('tools/list', {}, { 'X-CHANNEL': 'WechatApp' });
    const safeValues = wechatAppTools.tools[0].inputSchema.properties.safe.anyOf.map(option => option.const).sort();
    assert.deepEqual(safeValues, [0, 1]);
    const numericEnumHeaderCall = await rpc('tools/call', {
        name: 'send_push', arguments: { title: 'WechatApp enum header' },
    }, {
        'X-CHANNEL': 'WechatApp',
        'X-SAFE': '1',
        'X-MSGTYPE': 'text',
    });
    assert.equal(numericEnumHeaderCall.isError, true);
    assert.ok(JSON.parse(numericEnumHeaderCall.content[0].text).missing.includes('X-WECHAT-APP-CORPID'));

    const pushPlusHeaders = { 'X-CHANNEL': 'PushPlus', 'X-ARG-CHANNEL': 'webhook' };
    const pushPlusTools = await rpc('tools/list', {}, pushPlusHeaders);
    assert.equal(Object.hasOwn(pushPlusTools.tools[0].inputSchema.properties, 'channel'), false);
    const pushPlusHeaderCall = await rpc('tools/call', {
        name: 'send_push', arguments: { title: 'PushPlus channel header' },
    }, pushPlusHeaders);
    assert.equal(pushPlusHeaderCall.isError, true);
    assert.ok(JSON.parse(pushPlusHeaderCall.content[0].text).missing.includes('X-PUSH-PLUS-TOKEN'));

    const oneBotTools = await rpc('tools/list', {}, { 'X-CHANNEL': 'OneBot' });
    const oneBotSchemas = oneBotTools.tools[0].inputSchema.anyOf;
    assert.equal(oneBotSchemas.length, 2);
    const oneBotPrivate = oneBotSchemas.find(schema => schema.properties.message_type.const === 'private');
    const oneBotGroup = oneBotSchemas.find(schema => schema.properties.message_type.const === 'group');
    assert.ok(oneBotPrivate.required.includes('user_id'));
    assert.ok(!oneBotPrivate.required.includes('group_id'));
    assert.ok(oneBotGroup.required.includes('group_id'));
    assert.ok(!oneBotGroup.required.includes('user_id'));
    const oneBotMissingRecipient = await rpc('tools/call', {
        name: 'send_push', arguments: { title: 'OneBot recipient validation' },
    }, { 'X-CHANNEL': 'OneBot' });
    assert.equal(oneBotMissingRecipient.isError, true);
    assert.match(oneBotMissingRecipient.content[0].text, /Input validation error/);
    const fixedGroupTools = await rpc('tools/list', {}, { 'X-CHANNEL': 'OneBot', 'X-MESSAGE-TYPE': 'group' });
    const fixedGroupSchema = fixedGroupTools.tools[0].inputSchema;
    assert.equal(Object.hasOwn(fixedGroupSchema.properties, 'message_type'), false);
    assert.ok(fixedGroupSchema.required.includes('group_id'));

    const dingtalkTools = await rpc('tools/list', {}, { 'X-CHANNEL': 'Dingtalk' });
    const dingtalkProperties = dingtalkTools.tools[0].inputSchema.properties;
    assert.equal(dingtalkProperties.text.type, 'object');
    assert.equal(Object.hasOwn(dingtalkProperties.text, 'default'), false);
    assert.equal(dingtalkProperties.text.properties.content.type, 'string');
    assert.deepEqual(dingtalkProperties.actionCard.properties.btns.items.required, ['title', 'actionURL']);
    assert.deepEqual(dingtalkProperties.feedCard.properties.links.items.required, ['title', 'messageURL', 'picURL']);
    const invalidDingtalkHeader = await rpc('tools/call', {
        name: 'send_push', arguments: { title: 'Dingtalk nested validation' },
    }, { 'X-CHANNEL': 'Dingtalk', 'X-MARKDOWN': '{"text":2}' });
    assert.equal(invalidDingtalkHeader.isError, true);
    assert.match(JSON.parse(invalidDingtalkHeader.content[0].text).error, /X-MARKDOWN has an invalid value/);

    const serverChanTools = await rpc('tools/list', {}, { 'X-CHANNEL': 'ServerChanV3' });
    assert.equal(serverChanTools.tools[0].inputSchema.properties.tags.items.type, 'string');
    const wxPusherTools = await rpc('tools/list', {}, { 'X-CHANNEL': 'WxPusher' });
    assert.equal(wxPusherTools.tools[0].inputSchema.properties.topicIds.items.type, 'number');
    assert.equal(wxPusherTools.tools[0].inputSchema.properties.uids.items.type, 'string');
    const invalidArrayHeader = await rpc('tools/call', {
        name: 'send_push', arguments: { title: 'WxPusher item validation' },
    }, { 'X-CHANNEL': 'WxPusher', 'X-TOPIC-IDS': '["not-a-number"]' });
    assert.equal(invalidArrayHeader.isError, true);
    assert.match(JSON.parse(invalidArrayHeader.content[0].text).error, /X-TOPIC-IDS has an invalid value/);

    const ntfyTools = await rpc('tools/list');
    const ntfyFile = ntfyTools.tools[0].inputSchema.properties.file;
    assert.deepEqual(ntfyFile.required, ['name', 'size']);
    assert.equal(ntfyFile.properties.name.type, 'string');
    assert.equal(ntfyFile.properties.size.type, 'integer');

    const unselectedTools = await rpc('tools/list', {}, { 'X-CHANNEL': '' });
    assert.deepEqual(Object.keys(unselectedTools.tools[0].inputSchema.properties).sort(), ['body', 'title']);

    // Every published channel must produce a concrete tool schema from its metadata.
    for (const channel of Object.keys(push.PushAllInOne)) {
        const channelTools = await rpc('tools/list', {}, { 'X-CHANNEL': channel });
        const expectedProperties = new Set(['title', 'body', ...Object.keys(push.PushAllInOne[channel].optionSchema || {})]);
        const schemaBranches = channelTools.tools[0].inputSchema.anyOf || [channelTools.tools[0].inputSchema];
        for (const schema of schemaBranches) {
            assert.deepEqual(Object.keys(schema.properties).sort(), [...expectedProperties].sort(), channel);
        }
    }
    const missing = await rpc('tools/call', { name: 'send_push', arguments: { title: 'No send' } }, { 'X-CHANNEL': 'WechatRobot' });
    assert.equal(missing.isError, true);
    assert.ok(JSON.parse(missing.content[0].text).missing.includes('X-WECHAT-ROBOT-KEY'));
    const unselected = await rpc('tools/call', { name: 'send_push', arguments: { title: 'No channel' } }, { 'X-CHANNEL': '' });
    assert.equal(unselected.isError, true);
    // Separate requests run concurrently without sharing a transport/session.
    const sent = await Promise.all([1, 2].map(() => rpc('tools/call', {
        name: 'send_push', arguments: { title: 'Smoke' },
    })));
    assert.ok(sent.every(response => !response.isError));
    assert.equal(deliveries, 2);
    const rejected = await rpc('tools/call', {
        name: 'send_push', arguments: { title: 'Smoke' },
    });
    assert.equal(rejected.isError, true);
    assert.ok(!rejected.content[0].text.includes(token));
    assert.ok(!rejected.content[0].text.includes(ntfyAuth));
    assert.match(JSON.parse(rejected.content[0].text).data.errmsg, /\[redacted\]/);
    console.log('PASS: MCP handshake, auth, origin, dynamic channel arguments, header configuration, concurrent loopback pushes, provider errors and credential redaction');
} finally {
    fixture.closeAllConnections();
    fixture.close();
}
