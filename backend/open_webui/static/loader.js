(function () {
  var BOOT_TIMEOUT_MS = 7000;
  var RELOAD_GUARD_KEY = 'owui_loader_reload_once';
  var CHECK_INTERVAL_MS = 250;
  var checks = 0;
  var maxChecks = Math.ceil(BOOT_TIMEOUT_MS / CHECK_INTERVAL_MS);
  var booted = false;

  function markBooted() {
    booted = true;
    try {
      localStorage.removeItem(RELOAD_GUARD_KEY);
    } catch (e) {}
  }

  function hasSplash() {
    return !!document.getElementById('splash-screen');
  }

  function hasAppMounted() {
    if (!hasSplash()) return true;
    return !!document.querySelector("#app, #root, main, [data-testid='chat-container']");
  }

  function tryRecoverOnce() {
    var alreadyReloaded = false;
    try {
      alreadyReloaded = localStorage.getItem(RELOAD_GUARD_KEY) === '1';
    } catch (e) {
      alreadyReloaded = false;
    }

    if (!alreadyReloaded) {
      try {
        localStorage.setItem(RELOAD_GUARD_KEY, '1');
      } catch (e) {}
      var url = new URL(window.location.href);
      url.searchParams.set('_owui_refresh', String(Date.now()));
      window.location.replace(url.toString());
      return;
    }

    var splash = document.getElementById('splash-screen');
    if (!splash) return;

    var hint = document.createElement('div');
    hint.style.position = 'fixed';
    hint.style.left = '50%';
    hint.style.bottom = '8%';
    hint.style.transform = 'translateX(-50%)';
    hint.style.maxWidth = '560px';
    hint.style.padding = '10px 14px';
    hint.style.borderRadius = '10px';
    hint.style.background = 'rgba(0,0,0,0.65)';
    hint.style.color = '#fff';
    hint.style.fontSize = '13px';
    hint.style.lineHeight = '1.35';
    hint.style.zIndex = '120';
    hint.style.textAlign = 'center';
    hint.textContent =
      'Open WebUI завис на загрузке. Обновите страницу с очисткой кэша (Cmd+Shift+R) или очистите данные сайта для localhost:3000.';
    if (!document.getElementById('owui-loader-hint')) {
      hint.id = 'owui-loader-hint';
      splash.appendChild(hint);
    }
  }

  var observer = new MutationObserver(function () {
    if (!hasSplash()) {
      markBooted();
      observer.disconnect();
    }
  });
  observer.observe(document.documentElement, { childList: true, subtree: true });

  var timer = setInterval(function () {
    checks += 1;
    if (hasAppMounted()) {
      markBooted();
      clearInterval(timer);
      return;
    }
    if (checks >= maxChecks && !booted) {
      clearInterval(timer);
      tryRecoverOnce();
    }
  }, CHECK_INTERVAL_MS);
})();
