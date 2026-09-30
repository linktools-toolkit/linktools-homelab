// Uses only a loopback ntfy fixture. No real notification is sent.
import assert from 'node:assert/strict';
import { createServer } from 'node:http';
import { once } from 'node:events';

const base = process.env.MCP_PUSH_TEST_URL || 'http://127.0.0.1:8931';
const token = process.env.MCP_PUSH_TOKEN;
assert.ok(token);
let nextId = 0;
let deliveries = 0;
const fixture = createServer(async (req, res) => {
    let body = '';
    for await (const chunk of req) body += chunk;
    assert.equal(req.url, '/smoke-topic');
    assert.equal(body, 'hello from MCP');
    deliveries++;
    const data = deliveries > 2
        ? { errcode: 400, errmsg: `fixture rejection ${token}` }
        : { id: 'fixture-message', event: 'message' };
    res.writeHead(200, { 'Content-Type': 'application/json' }).end(JSON.stringify(data));
});
fixture.listen(18932, '127.0.0.1');
await once(fixture, 'listening');

async function rpc(method, params = {}) {
    const response = await fetch(`${base}/mcp`, {
        method: 'POST',
        headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json',
            Accept: 'application/json, text/event-stream',
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
    assert.deepEqual(tools.tools.map(tool => tool.name).sort(), ['list_push_channels', 'send_push']);
    const listed = await rpc('tools/call', { name: 'list_push_channels', arguments: {} });
    const channels = JSON.parse(listed.content[0].text);
    assert.ok(channels.find(channel => channel.channel === 'Ntfy').configured);
    assert.ok(!channels.find(channel => channel.channel === 'WechatRobot').configured);
    assert.ok(!listed.content[0].text.includes(token));
    const missing = await rpc('tools/call', { name: 'send_push', arguments: { channel: 'WechatRobot', title: 'No send' } });
    assert.equal(missing.isError, true);
    // Separate requests run concurrently without sharing a transport/session.
    const sent = await Promise.all([1, 2].map(() => rpc('tools/call', {
        name: 'send_push', arguments: { channel: 'Ntfy', title: 'Smoke', body: 'hello from MCP' },
    })));
    assert.ok(sent.every(response => !response.isError));
    assert.equal(deliveries, 2);
    const rejected = await rpc('tools/call', {
        name: 'send_push', arguments: { channel: 'Ntfy', title: 'Smoke', body: 'hello from MCP' },
    });
    assert.equal(rejected.isError, true);
    assert.ok(!rejected.content[0].text.includes(token));
    assert.match(JSON.parse(rejected.content[0].text).data.errmsg, /\[redacted\]/);
    console.log('PASS: MCP handshake, auth, origin, discovery, missing config, concurrent loopback pushes, provider errors and credential redaction');
} finally {
    fixture.closeAllConnections();
    fixture.close();
}
