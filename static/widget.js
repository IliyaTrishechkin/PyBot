// static/widget.js
(function () {
    const scriptEl =
        document.currentScript ||
        Array.from(document.getElementsByTagName('script')).find((s) =>
            (s.src || '').includes('widget.js')
        );

    const srcUrl = (() => {
        try {
            return new URL(scriptEl?.src || '');
        } catch {
            return null;
        }
    })();

    const apiOverride = scriptEl?.dataset?.api;
    const wsOverride = scriptEl?.dataset?.ws;

    const origin = srcUrl?.origin || `${location.protocol}//${location.host}`;
    const proto =
        (srcUrl?.protocol || location.protocol) === 'https:' ? 'wss' : 'ws';

    const API_BASE = apiOverride || origin;
    const WS_BASE = wsOverride || `${proto}://${srcUrl?.host || location.host}`;

    const THEME = {
        accent: '#FFC107',
        accentHover: '#FFB300',
        dark: '#1F2A44',
    };

    const launcher = document.createElement('button');
    launcher.id = 'chat-launcher';
    launcher.setAttribute('aria-expanded', 'false');
    launcher.style = `
    position: fixed; right: 20px; bottom: 20px;
    background: ${THEME.accent}; color: ${THEME.dark}; border: none;
    padding: 10px 16px; border-radius: 999px;
    box-shadow: 0 4px 12px rgba(0,0,0,.15);
    cursor: pointer; font-family: sans-serif; font-size: 14px;
    display: flex; align-items: center; gap: 8px; z-index: 10000;
  `;
    launcher.innerHTML = `<span style="
    display:inline-block;width:10px;height:10px;border-radius:50%;
    background:#2ecc71;border:2px solid #e8f5e9;"></span> Напишіть нам, ми онлайн!`;
    document.body.appendChild(launcher);

    const chat = document.createElement('div');
    chat.id = 'chat-widget';
    chat.style = `
    position: fixed; right: 20px; bottom: 70px;
    width: 340px; max-height: 520px; background:#fff;
    border: 1px solid #ddd; border-radius: 8px;
    display: none; flex-direction: column;
    box-shadow: 0 8px 24px rgba(0,0,0,.15);
    font-family: sans-serif; font-size: 14px; z-index: 10000;
  `;

    const header = document.createElement('div');
    header.style = `
    background:${THEME.accent}; color:${THEME.dark}; padding:10px 12px;
    border-radius: 8px 8px 0 0; font-weight:600;
    display:flex; align-items:center; justify-content:space-between;
  `;
    header.innerHTML = `<span>Чат підтримки</span>`;
    chat.appendChild(header);

    const messages = document.createElement('div');
    messages.style = `flex:1; overflow-y:auto; padding:10px; box-sizing:border-box;`;
    chat.appendChild(messages);

    const quickRow = document.createElement('div');
    quickRow.style = `
    display:flex; flex-wrap:wrap; gap:8px; padding:8px 10px; border-top:1px solid #f0f0f0;
  `;
    chat.appendChild(quickRow);

    const inputRow = document.createElement('div');
    inputRow.style = `display:flex; border-top:1px solid #eee; padding:8px; gap:8px;`;
    const input = document.createElement('input');
    input.type = 'text';
    input.placeholder = 'Напишіть повідомлення…';
    input.style =
        'flex:1; border:1px solid #ddd; border-radius:6px; padding:8px;';
    const sendBtn = document.createElement('button');
    sendBtn.textContent = 'Надіслати';
    sendBtn.style = `
    border:1px solid ${THEME.accentHover};
    padding:8px 12px; background:${THEME.accent}; color:${THEME.dark};
    border-radius:6px; cursor:pointer;
  `;
    sendBtn.onmouseenter = () => (sendBtn.style.background = THEME.accentHover);
    sendBtn.onmouseleave = () => (sendBtn.style.background = THEME.accent);

    inputRow.appendChild(input);
    inputRow.appendChild(sendBtn);
    chat.appendChild(inputRow);

    document.body.appendChild(chat);

    let sessionId = localStorage.getItem('chat_session');
    if (!sessionId) {
        sessionId = Math.random().toString(36).substr(2, 9);
        localStorage.setItem('chat_session', sessionId);
    }

    let ws;
    let bootLoaded = false;

    function addBotMessage(text) {
        const d = document.createElement('div');
        d.innerHTML = linkify(String(text)).replace(/\n/g, '<br>');
        d.style = 'margin:6px 0; color:#007bff;';
        messages.appendChild(d);
        messages.scrollTop = messages.scrollHeight;
    }

    function addUserMessage(text) {
        const d = document.createElement('div');
        d.textContent = text;
        d.style = 'margin:6px 0; text-align:right; color:#333;';
        messages.appendChild(d);
        messages.scrollTop = messages.scrollHeight;
    }

    function renderQuickButtons(options) {
        quickRow.innerHTML = '';
        options.forEach((label) => {
            const b = document.createElement('button');
            b.textContent = label;
            b.style = `
        background:#fff; border:1px solid ${THEME.accent}; color:${THEME.dark};
        border-radius:999px; padding:6px 10px; cursor:pointer;
      `;
            b.onmouseenter = () => (b.style.background = '#FFF7D1');
            b.onmouseleave = () => (b.style.background = '#fff');

            b.onclick = () => {
                addUserMessage(label);
                sendToApi(label);
            };
            quickRow.appendChild(b);
        });
    }

    async function loadBootstrap() {
        if (bootLoaded) return;
        try {
            const r = await fetch(`${API_BASE}/api/next`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ session_id: sessionId, text: '' }),
            });
            if (r.ok) {
                const data = await r.json();
                if (data.message) addBotMessage(data.message);
                if (Array.isArray(data.options))
                    renderQuickButtons(data.options);
                bootLoaded = true;
            }
        } catch (_) {}
    }

    async function sendToApi(text) {
        try {
            const r = await fetch(`${API_BASE}/api/next`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ session_id: sessionId, text }),
            });
            if (r.ok) {
                const data = await r.json();
                if (data.message) addBotMessage(data.message);
                if (Array.isArray(data.options))
                    renderQuickButtons(data.options);
            }
        } catch (_) {
            const err = document.createElement('div');
            err.textContent = 'Не вдалося надіслати повідомлення';
            err.style = 'margin:6px 0; color:red;';
            messages.appendChild(err);
        }
    }

    function ensureWS() {
        if (ws && ws.readyState === WebSocket.OPEN) return;
        ws = new WebSocket(`${WS_BASE}/ws/${sessionId}`);
        ws.onmessage = (e) => addBotMessage(e.data);
        ws.onerror = () => {
            const err = document.createElement('div');
            err.textContent = 'Помилка з’єднання з чатом';
            err.style = 'margin:6px 0; color:red;';
            messages.appendChild(err);
        };
    }

    function escapeHtml(str) {
        return str.replace(
            /[&<>"']/g,
            (m) =>
                ({
                    '&': '&amp;',
                    '<': '&lt;',
                    '>': '&gt;',
                    '"': '&quot;',
                    "'": '&#39;',
                }[m])
        );
    }

    function linkify(text) {
        const esc = escapeHtml(text);
        const urlRe = /(https?:\/\/[^\s<]+)/g;
        return esc.replace(
            urlRe,
            (url) =>
                `<a href="${url}" target="_blank" rel="noopener noreferrer">${url}</a>`
        );
    }

    sendBtn.onclick = () => {
        const text = input.value.trim();
        if (!text) return;
        addUserMessage(text);
        input.value = '';
        sendToApi(text);
    };
    input.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendBtn.click();
    });

    launcher.onclick = () => {
        const opened = chat.style.display === 'flex';
        if (opened) {
            chat.style.display = 'none';
            launcher.setAttribute('aria-expanded', 'false');
        } else {
            chat.style.display = 'flex';
            launcher.setAttribute('aria-expanded', 'true');
            ensureWS();
            loadBootstrap();
        }
    };
})();
