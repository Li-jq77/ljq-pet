(function () {
    var root = document.getElementById("dodouWidget");
    if (!root) return;

    var panel = document.getElementById("dodouPanel");
    var fab = document.getElementById("dodouFab");
    var messagesEl = document.getElementById("dodouMessages");
    var form = document.getElementById("dodouForm");
    var input = document.getElementById("dodouInput");
    var minimizeBtn = document.getElementById("dodouMinimize");
    var closeBtn = document.getElementById("dodouClose");
    var tokenInput = form.querySelector('input[name="csrfmiddlewaretoken"]');
    var chatUrl = root.getAttribute("data-chat-url");

    var positionKey = "dodouFabPosition";
    var panelPositionKey = "dodouPanelPosition";
    var locationKey = "dodouLocation";
    var dragging = false;
    var moved = false;
    var startX = 0;
    var startY = 0;
    var originLeft = 0;
    var originTop = 0;
    var isSending = false;
    var history = [];
    var panelHead = panel.querySelector(".dodou-panel-head");
    var panelDrag = {
        active: false,
        moved: false,
        startX: 0,
        startY: 0,
        originLeft: 0,
        originTop: 0
    };

    root.classList.add("is-ready");

    function clamp(value, min, max) {
        return Math.min(Math.max(value, min), max);
    }

    function loadFabPosition() {
        var stored = null;
        try {
            stored = JSON.parse(localStorage.getItem(positionKey) || "null");
        } catch (e) {
            stored = null;
        }
        if (!stored || !isFinite(stored.left) || !isFinite(stored.top)) return;
        applyFabPosition(stored.left, stored.top, true);
    }

    function applyFabPosition(left, top, fromStorage) {
        var rect = fab.getBoundingClientRect();
        var width = fromStorage ? rect.width || 76 : rect.width;
        var height = fromStorage ? rect.height || 58 : rect.height;
        left = clamp(left, 8, Math.max(8, window.innerWidth - width - 8));
        top = clamp(top, 8, Math.max(8, window.innerHeight - height - 8));
        fab.style.right = "auto";
        fab.style.left = left + "px";
        fab.style.top = top + "px";
    }

    function saveFabPosition() {
        var rect = fab.getBoundingClientRect();
        try {
            localStorage.setItem(positionKey, JSON.stringify({
                left: rect.left,
                top: rect.top
            }));
        } catch (e) {}
    }

    function applyPanelPosition(left, top, fromStorage) {
        var rect = panel.getBoundingClientRect();
        var width = fromStorage ? rect.width || 380 : rect.width;
        var height = fromStorage ? rect.height || 540 : rect.height;
        left = clamp(left, 8, Math.max(8, window.innerWidth - width - 8));
        top = clamp(top, 8, Math.max(8, window.innerHeight - height - 8));
        panel.style.right = "auto";
        panel.style.bottom = "auto";
        panel.style.left = left + "px";
        panel.style.top = top + "px";
    }

    function savePanelPosition() {
        var rect = panel.getBoundingClientRect();
        try {
            localStorage.setItem(panelPositionKey, JSON.stringify({
                left: rect.left,
                top: rect.top
            }));
        } catch (e) {}
    }

    function loadPanelPosition() {
        var stored = null;
        try {
            stored = JSON.parse(localStorage.getItem(panelPositionKey) || "null");
        } catch (e) {
            stored = null;
        }
        if (!stored || !isFinite(stored.left) || !isFinite(stored.top)) return;
        applyPanelPosition(stored.left, stored.top, true);
    }

    function isPanelOpen() {
        return panel.classList.contains("is-open");
    }

    function togglePanel(forceOpen) {
        var shouldOpen = forceOpen === undefined ? !isPanelOpen() : forceOpen;
        panel.classList.toggle("is-open", shouldOpen);
        root.classList.toggle("is-open", shouldOpen);
        panel.setAttribute("aria-hidden", shouldOpen ? "false" : "true");
        fab.setAttribute("aria-expanded", shouldOpen ? "true" : "false");
        if (shouldOpen) {
            scrollToBottom();
            window.setTimeout(function () {
                input.focus();
            }, 120);
        }
    }

    function scrollToBottom() {
        messagesEl.scrollTop = messagesEl.scrollHeight;
    }

    function appendMessage(text, sender, options) {
        options = options || {};
        var row = document.createElement("div");
        row.className = "dodou-row dodou-row-" + sender;

        var content = document.createElement("div");
        content.className = "dodou-content";

        if (sender === "bot") {
            var avatar = document.createElement("span");
            avatar.className = "dodou-avatar";
            avatar.setAttribute("aria-hidden", "true");
            avatar.textContent = "豆";
            row.appendChild(avatar);

            var bubble = document.createElement("div");
            bubble.className = "dodou-bubble" + (options.kind === "weather" ? " dodou-bubble-weather" : "");
            bubble.textContent = text;
            content.appendChild(bubble);
        } else {
            var userBubble = document.createElement("div");
            userBubble.className = "dodou-bubble dodou-bubble-user";
            userBubble.textContent = text;
            content.appendChild(userBubble);
        }

        row.appendChild(content);
        messagesEl.appendChild(row);
        scrollToBottom();
        return row;
    }

    function addTyping() {
        var row = document.createElement("div");
        row.className = "dodou-row dodou-row-bot dodou-typing-row";
        row.innerHTML = '<span class="dodou-avatar" aria-hidden="true">豆</span>' +
            '<div class="dodou-content"><div class="dodou-bubble dodou-typing">' +
            '<span></span><span></span><span></span></div></div>';
        messagesEl.appendChild(row);
        scrollToBottom();
        return row;
    }

    function wait(ms) {
        return new Promise(function (resolve) {
            window.setTimeout(resolve, ms);
        });
    }

    function getStoredLocation() {
        try {
            var location = JSON.parse(localStorage.getItem(locationKey) || "null");
            if (location && isFinite(location.lat) && isFinite(location.lon)) return location;
        } catch (e) {}
        return null;
    }

    function requestLocation() {
        var stored = getStoredLocation();
        if (stored) return Promise.resolve(stored);
        if (!("geolocation" in navigator)) return Promise.resolve(null);

        return new Promise(function (resolve) {
            var settled = false;
            function finish(location) {
                if (settled) return;
                settled = true;
                if (location) {
                    try {
                        localStorage.setItem(locationKey, JSON.stringify(location));
                    } catch (e) {}
                }
                resolve(location);
            }
            navigator.geolocation.getCurrentPosition(function (position) {
                finish({
                    lat: position.coords.latitude,
                    lon: position.coords.longitude
                });
            }, function () {
                finish(null);
            }, {
                timeout: 6000,
                maximumAge: 600000
            });
        });
    }

    function looksLikeWeather(text) {
        var keywords = ["天气", "下雨", "遛狗", "适合遛", "出去遛", "适合散步", "出去散步", "出门遛", "风力", "降温", "气温", "预报"];
        return keywords.some(function (keyword) {
            return text.indexOf(keyword) !== -1;
        });
    }

    function setComposerDisabled(disabled) {
        input.disabled = disabled;
        var sendButton = form.querySelector(".dodou-send");
        sendButton.disabled = disabled;
    }

    async function sendMessage(rawText, options) {
        var text = (rawText || "").replace(/\s+/g, " ").trim();
        options = options || {};
        if (!text || isSending) return;

        appendMessage(text, "user");
        history.push({ role: "user", content: text });
        if (history.length > 16) history = history.slice(-16);
        input.value = "";
        isSending = true;
        setComposerDisabled(true);
        var typing = addTyping();

        var body = {
            message: text,
            history: history.slice(-8)
        };

        if (options.locate && looksLikeWeather(text)) {
            var location = await requestLocation();
            if (location) {
                body.location = location;
            } else {
                typing.remove();
                var locationPrompt = "豆豆没有拿到定位，可以输入城市名，例如“北京遛狗天气”。";
                appendMessage(locationPrompt, "bot");
                history.push({ role: "assistant", content: locationPrompt });
                isSending = false;
                setComposerDisabled(false);
                input.focus();
                return;
            }
        }

        var payload;
        try {
            payload = await fetch(chatUrl, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": tokenInput ? tokenInput.value : "",
                    "X-Requested-With": "XMLHttpRequest"
                },
                body: JSON.stringify(body)
            });
        } catch (e) {
            typing.remove();
            appendMessage("豆豆这边暂时连接不上，请刷新页面后再试。", "bot");
            isSending = false;
            setComposerDisabled(false);
            input.focus();
            return;
        }

        await wait(260);
        typing.remove();

        if (!payload.ok) {
            appendMessage("豆豆这次没听清，换个说法再问一次吧。", "bot");
        } else {
            var data;
            try {
                data = await payload.json();
            } catch (e) {
                data = null;
            }
            var replyText = (data && data.text) || "豆豆先记下了，再具体说说宠物的情况好吗？";
            appendMessage(replyText, "bot", { kind: data && data.kind === "weather" ? "weather" : "" });
            history.push({ role: "assistant", content: replyText });
        }

        isSending = false;
        setComposerDisabled(false);
        input.focus();
    }

    function sendFromQuick(button) {
        var quick = button.getAttribute("data-quick");
        if (!quick) return;
        sendMessage(quick, {
            locate: button.hasAttribute("data-locate")
        });
    }

    form.addEventListener("submit", function (event) {
        event.preventDefault();
        sendMessage(input.value);
    });

    document.addEventListener("click", function (event) {
        var action = event.target.closest(".dodou-action, .dodou-suggestion");
        if (action && root.contains(action)) {
            sendFromQuick(action);
        }
    });

    fab.addEventListener("pointerdown", function (event) {
        if (event.button !== 0 && event.pointerType === "mouse") return;
        dragging = true;
        moved = false;
        startX = event.clientX;
        startY = event.clientY;
        var rect = fab.getBoundingClientRect();
        originLeft = rect.left;
        originTop = rect.top;
        fab.setPointerCapture && fab.setPointerCapture(event.pointerId);
        fab.classList.add("is-dragging");
    });

    fab.addEventListener("pointermove", function (event) {
        if (!dragging) return;
        var dx = event.clientX - startX;
        var dy = event.clientY - startY;
        if (Math.abs(dx) + Math.abs(dy) > 4) moved = true;
        if (moved) {
            applyFabPosition(originLeft + dx, originTop + dy);
            document.body.style.userSelect = "none";
            document.body.style.webkitUserSelect = "none";
        }
    });

    function endDrag(event) {
        if (!dragging) return;
        dragging = false;
        fab.classList.remove("is-dragging");
        fab.releasePointerCapture && event.pointerId && fab.releasePointerCapture(event.pointerId);
        document.body.style.userSelect = "";
        document.body.style.webkitUserSelect = "";
        if (moved) {
            saveFabPosition();
            if (isPanelOpen()) togglePanel(false);
        }
    }

    fab.addEventListener("pointerup", endDrag);
    fab.addEventListener("pointercancel", endDrag);

    panelHead.addEventListener("pointerdown", function (event) {
        if (event.button !== 0 && event.pointerType === "mouse") return;
        var interactive = event.target.closest("button, a, input, textarea");
        if (interactive) return;
        panelDrag.active = true;
        panelDrag.moved = false;
        panelDrag.startX = event.clientX;
        panelDrag.startY = event.clientY;
        var rect = panel.getBoundingClientRect();
        panelDrag.originLeft = rect.left;
        panelDrag.originTop = rect.top;
        panelHead.setPointerCapture && panelHead.setPointerCapture(event.pointerId);
        panelHead.classList.add("is-dragging");
        panel.classList.add("is-dragging");
    });

    panelHead.addEventListener("pointermove", function (event) {
        if (!panelDrag.active) return;
        var dx = event.clientX - panelDrag.startX;
        var dy = event.clientY - panelDrag.startY;
        if (Math.abs(dx) + Math.abs(dy) > 4) panelDrag.moved = true;
        if (panelDrag.moved) {
            applyPanelPosition(
                panelDrag.originLeft + dx,
                panelDrag.originTop + dy
            );
            document.body.style.userSelect = "none";
            document.body.style.webkitUserSelect = "none";
        }
    });

    function endPanelDrag(event) {
        if (!panelDrag.active) return;
        panelDrag.active = false;
        panelHead.classList.remove("is-dragging");
        panel.classList.remove("is-dragging");
        panelHead.releasePointerCapture &&
            event.pointerId &&
            panelHead.releasePointerCapture(event.pointerId);
        document.body.style.userSelect = "";
        document.body.style.webkitUserSelect = "";
        if (panelDrag.moved) savePanelPosition();
    }

    panelHead.addEventListener("pointerup", endPanelDrag);
    panelHead.addEventListener("pointercancel", endPanelDrag);

    fab.addEventListener("click", function (event) {
        if (moved) {
            event.stopPropagation();
            return;
        }
        togglePanel();
    });

    minimizeBtn.addEventListener("click", function () {
        togglePanel(false);
        input.blur();
    });

    closeBtn.addEventListener("click", function () {
        togglePanel(false);
        input.blur();
    });

    window.addEventListener("resize", function () {
        var rect = fab.getBoundingClientRect();
        applyFabPosition(rect.left, rect.top, true);
    });

    loadFabPosition();
    loadPanelPosition();
})();
