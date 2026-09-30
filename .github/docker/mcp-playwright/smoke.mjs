import assert from 'node:assert/strict';

const page = await fetch('http://127.0.0.1:6080/vnc.html');
assert.equal(page.status, 200);
assert.match(await page.text(), /noVNC/);

// Verify the WebSocket proxy reaches the VNC server, beyond static HTML.
await new Promise((resolve, reject) => {
  const ws = new WebSocket('ws://127.0.0.1:6080/websockify', ['binary']);
  ws.binaryType = 'arraybuffer';
  const timer = setTimeout(() => {
    ws.close();
    reject(new Error('VNC handshake timed out'));
  }, 10000);
  ws.onmessage = ({ data }) => {
    clearTimeout(timer);
    ws.close();
    try {
      assert.match(new TextDecoder().decode(data), /^RFB /);
      resolve();
    } catch (error) {
      reject(error);
    }
  };
  ws.onerror = () => {
    clearTimeout(timer);
    reject(new Error('noVNC WebSocket failed'));
  };
});

let session;
async function rpc(message) {
  const response = await fetch('http://127.0.0.1:8931/mcp', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'application/json, text/event-stream',
      ...(session ? { 'Mcp-Session-Id': session } : {}),
    },
    body: JSON.stringify({ jsonrpc: '2.0', ...message }),
    signal: AbortSignal.timeout(30000),
  });
  assert.ok(response.ok, `MCP returned HTTP ${response.status}`);
  session = response.headers.get('mcp-session-id') || session;
  if (message.id === undefined) return;
  const text = await response.text();
  const result = response.headers.get('content-type')?.includes('text/event-stream')
    ? text.split('\n').filter(line => line.startsWith('data:'))
      .map(line => JSON.parse(line.slice(5))).find(item => item.id === message.id)
    : JSON.parse(text);
  assert.ok(result, `No MCP response for ${message.id}`);
  assert.equal(result.error, undefined, JSON.stringify(result.error));
  assert.notEqual(result.result?.isError, true, JSON.stringify(result.result));
  return result.result;
}

await rpc({ id: 1, method: 'initialize', params: {
  protocolVersion: '2024-11-05', capabilities: {},
  clientInfo: { name: 'container-smoke-test', version: '1' },
} });
await rpc({ method: 'notifications/initialized' });
const url = 'http://127.0.0.1:6080/vnc.html';
await rpc({ id: 2, method: 'tools/call', params: {
  name: 'browser_navigate', arguments: { url },
} });
const tabs = await (await fetch('http://127.0.0.1:9222/json/list')).json();
assert.ok(tabs.some(tab => tab.type === 'page' && tab.url === url),
  'MCP must navigate the same Chromium instance shown by noVNC');
console.log('Browser, noVNC WebSocket and shared MCP browser checks passed');
