/* ehr2rl site behavior, layered on Furo without replacing its markup.
 *
 * 1. In-place navigation: internal links swap the article, footer, and
 *    "On this page" contents instead of reloading, so the sidebar stays put.
 *    Anything unexpected falls back to a normal page load.
 * 2. Live search: the sidebar search box shows results while typing, using
 *    Sphinx's own search index and ranking. Enter still opens the full
 *    search page.
 * 3. Contents tracking: marks the section being read in "On this page".
 *    Replaces Furo's tracker, which binds to the first page's links only.
 */
(() => {
  "use strict";

  // This file lives at <root>/_static/site.js.
  const ROOT = new URL("..", document.currentScript.src);
  const EXCLUDED_PAGES = new Set(["search.html", "genindex.html"]);
  const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");

  // ---------------------------------------------------------------------------
  // In-place navigation
  // ---------------------------------------------------------------------------
  const pageCache = new Map();
  let currentPath = location.pathname;
  let navigationId = 0;

  function isSoftNavigable(url) {
    if (url.origin !== location.origin || !url.href.startsWith(ROOT.href)) return false;
    const relative = url.pathname.slice(ROOT.pathname.length);
    if (relative.startsWith("_static/") || relative.startsWith("_sources/")) return false;
    if (EXCLUDED_PAGES.has(relative)) return false;
    return relative === "" || relative.endsWith("/") || relative.endsWith(".html");
  }

  function fetchPage(url) {
    const key = url.pathname;
    if (!pageCache.has(key)) {
      const request = fetch(key, { credentials: "same-origin" }).then((response) => {
        const type = response.headers.get("content-type") || "";
        if (!response.ok || !type.includes("text/html")) throw new Error(`HTTP ${response.status}`);
        return response.text();
      });
      request.catch(() => pageCache.delete(key));
      pageCache.set(key, request);
      if (pageCache.size > 30) pageCache.delete(pageCache.keys().next().value);
    }
    return pageCache.get(key);
  }

  function wait(ms) {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }

  async function navigate(url, { push = true, restoreY = null } = {}) {
    const id = ++navigationId;
    const main = document.querySelector(".main");
    if (push) history.replaceState({ ...history.state, y: window.scrollY }, "");
    main?.classList.add("is-leaving");

    let doc;
    try {
      const [html] = await Promise.all([fetchPage(url), wait(prefersReducedMotion.matches ? 0 : 90)]);
      doc = new DOMParser().parseFromString(html, "text/html");
      if (!doc.querySelector(".article-container")) throw new Error("unexpected page layout");
    } catch {
      location.assign(url.href);
      return;
    }
    if (id !== navigationId) return; // a newer navigation started meanwhile

    if (push) history.pushState({ y: 0 }, "", url.href);
    swapPage(doc);
    currentPath = location.pathname;
    main?.classList.remove("is-leaving");

    if (restoreY !== null) {
      window.scrollTo({ top: restoreY, behavior: "instant" });
    } else {
      // pushState does not update :target, so apply Furo's scroll margin here.
      const target = url.hash && document.getElementById(decodeURIComponent(url.hash.slice(1)));
      const top = target ? target.getBoundingClientRect().top + window.scrollY - scrollMargin() : 0;
      window.scrollTo({ top, behavior: "instant" });
    }

    const heading = document.querySelector("article[role='main'] h1");
    if (heading) {
      heading.setAttribute("tabindex", "-1");
      heading.focus({ preventScroll: true });
    }
    setupContentsTracking();
  }

  function swapPage(doc) {
    document.title = doc.title;
    const root = doc.documentElement.dataset.content_root;
    if (root !== undefined) document.documentElement.dataset.content_root = root;

    // Keep the live theme toggle: Furo attached its click handler to this node.
    const themeToggle = document.querySelector(".theme-toggle-content");

    for (const selector of [".article-container", ".content > footer"]) {
      const current = document.querySelector(selector);
      const next = doc.querySelector(selector);
      if (current && next) current.replaceWith(document.adoptNode(next));
    }
    const newToggle = document.querySelector(".theme-toggle-content");
    if (themeToggle && newToggle) newToggle.replaceWith(themeToggle);

    // "On this page": class (no-toc) and contents.
    const toc = document.querySelector(".toc-drawer");
    const nextToc = doc.querySelector(".toc-drawer");
    if (toc && nextToc) {
      toc.className = nextToc.className;
      toc.innerHTML = nextToc.innerHTML;
    }
    const tocIcon = document.querySelector(".toc-header-icon");
    const nextTocIcon = doc.querySelector(".toc-header-icon");
    if (tocIcon && nextTocIcon) tocIcon.className = nextTocIcon.className;

    // Left navigation: update which page is current, keeping its scroll position.
    const scroller = document.querySelector(".sidebar-scroll");
    const scrollTop = scroller ? scroller.scrollTop : 0;
    const tree = document.querySelector(".sidebar-tree");
    const nextTree = doc.querySelector(".sidebar-tree");
    if (tree && nextTree) tree.innerHTML = nextTree.innerHTML;
    if (scroller) scroller.scrollTop = scrollTop;

    // Close the mobile drawers.
    for (const toggle of document.querySelectorAll("#__navigation, #__toc")) toggle.checked = false;
  }

  function linkFromEvent(event) {
    const link = event.target.closest?.("a[href]");
    if (!link || link.hasAttribute("download")) return null;
    if (link.target && link.target !== "_self") return null;
    return link;
  }

  document.addEventListener("click", (event) => {
    if (event.defaultPrevented || event.button !== 0) return;
    if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
    const link = linkFromEvent(event);
    if (!link) return;
    const url = new URL(link.href, location.href);
    if (!isSoftNavigable(url)) return;
    if (url.pathname === location.pathname && url.search === location.search) {
      if (url.hash) return; // in-page anchor: let the browser scroll
      event.preventDefault();
      window.scrollTo({ top: 0, behavior: "smooth" });
      return;
    }
    event.preventDefault();
    navigate(url);
  });

  // Start fetching a page as soon as the pointer rests on its link.
  let prefetchTimer = null;
  document.addEventListener("pointerover", (event) => {
    const link = linkFromEvent(event);
    if (!link) return;
    clearTimeout(prefetchTimer);
    prefetchTimer = setTimeout(() => {
      const url = new URL(link.href, location.href);
      if (isSoftNavigable(url) && url.pathname !== location.pathname) fetchPage(url).catch(() => {});
    }, 60);
  });

  window.addEventListener("popstate", (event) => {
    if (location.pathname === currentPath) return; // hash change on the same page
    navigate(new URL(location.href), { push: false, restoreY: event.state?.y ?? 0 });
  });
  if ("scrollRestoration" in history) history.scrollRestoration = "manual";
  history.replaceState({ ...history.state, y: window.scrollY }, "");

  // ---------------------------------------------------------------------------
  // "On this page" tracking
  // ---------------------------------------------------------------------------
  let tocItems = [];
  let pinnedItem = null;

  function setupContentsTracking() {
    pinnedItem = null;
    tocItems = Array.from(document.querySelectorAll(".toc-tree a.reference")).map((link) => {
      const href = link.getAttribute("href") || "";
      const id = href.startsWith("#") ? decodeURIComponent(href.slice(1)) : null;
      return { item: link.parentElement, target: id ? document.getElementById(id) : null, href };
    });
    updateContentsTracking();
  }

  // Matches Furo's :target scroll margin: below the mobile header, plus 2.5rem.
  function scrollMargin() {
    const header = document.querySelector(".mobile-header");
    const headerHeight =
      header && getComputedStyle(header).display !== "none" ? header.getBoundingClientRect().height : 0;
    const rem = parseFloat(getComputedStyle(document.documentElement).fontSize);
    return headerHeight + 2.5 * rem;
  }

  function trackingThreshold() {
    return scrollMargin() + 8;
  }

  function updateContentsTracking() {
    if (!tocItems.length) return;
    let current = pinnedItem;
    if (!current) {
      const threshold = trackingThreshold();
      current = tocItems[0];
      for (const entry of tocItems) {
        if (!entry.target) continue;
        if (entry.target.getBoundingClientRect().top <= threshold) current = entry;
        else break;
      }
      const atBottom = window.innerHeight + window.scrollY >= document.documentElement.scrollHeight - 2;
      if (atBottom && window.scrollY > 0) current = tocItems[tocItems.length - 1];
    }
    for (const entry of tocItems) entry.item.classList.toggle("toc-current", entry === current);
    if (window.scrollY === 0) document.querySelector(".toc-scroll")?.scrollTo(0, 0);
  }

  let trackingFrame = 0;
  function scheduleTracking() {
    if (trackingFrame) return;
    trackingFrame = requestAnimationFrame(() => {
      trackingFrame = 0;
      updateContentsTracking();
    });
  }
  window.addEventListener("scroll", scheduleTracking, { passive: true });
  window.addEventListener("resize", scheduleTracking, { passive: true });

  // A clicked entry stays marked until the reader scrolls themselves, even if
  // the page cannot scroll far enough to bring that section to the top.
  document.addEventListener("click", (event) => {
    const link = event.target.closest?.(".toc-tree a.reference");
    if (!link) return;
    pinnedItem = tocItems.find((entry) => entry.item === link.parentElement) || null;
    updateContentsTracking();
  });
  const unpin = () => {
    if (pinnedItem) {
      pinnedItem = null;
      scheduleTracking();
    }
  };
  window.addEventListener("wheel", unpin, { passive: true });
  window.addEventListener("touchmove", unpin, { passive: true });
  window.addEventListener("keydown", (event) => {
    if (["ArrowUp", "ArrowDown", "PageUp", "PageDown", "Home", "End", " "].includes(event.key)) unpin();
  });

  // ---------------------------------------------------------------------------
  // Live search
  // ---------------------------------------------------------------------------
  const MAX_RESULTS = 8;
  const KIND_LABELS = { object: "API", title: "Section", text: "Page", index: "Index" };
  let searchReady = null;

  function loadScript(src) {
    return new Promise((resolve, reject) => {
      const script = document.createElement("script");
      script.src = src;
      script.onload = resolve;
      script.onerror = () => reject(new Error(`could not load ${src}`));
      document.head.appendChild(script);
    });
  }

  function searchApi() {
    return typeof Search !== "undefined" ? Search : null; // global from searchtools.js
  }

  // Load Sphinx's search engine and index once, on first use.
  function ensureSearch() {
    if (searchReady) return searchReady;
    searchReady = (async () => {
      if (!searchApi()) {
        if (typeof Stemmer === "undefined") await loadScript(new URL("_static/language_data.js", ROOT).href);
        // On load, searchtools.js overwrites every input[name="q"] with the
        // URL's ?q= value, which would erase what is being typed. Unname the
        // boxes while it loads.
        const boxes = Array.from(document.querySelectorAll("input[name='q']"));
        boxes.forEach((box) => box.removeAttribute("name"));
        try {
          await loadScript(new URL("_static/searchtools.js", ROOT).href);
        } finally {
          boxes.forEach((box) => box.setAttribute("name", "q"));
        }
      }
      if (!searchApi().hasIndex()) await loadScript(new URL("searchindex.js", ROOT).href);
      return searchApi();
    })();
    searchReady.catch(() => (searchReady = null));
    return searchReady;
  }

  function runSearch(api, query) {
    const parsed = api._parseQuery(query);
    // Sphinx stores terms so the next page highlights them; this site does not.
    try {
      localStorage.removeItem("sphinx_highlight_terms");
    } catch {}
    const ranked = api._performSearch(...parsed).reverse(); // Sphinx order, best first
    // For a quick-results list, put titles that match what was typed first,
    // keeping Sphinx's order otherwise.
    const typed = query.toLowerCase();
    const titleMatch = ([, title]) => {
      const full = title.toLowerCase();
      const last = full.split(" > ").pop().split(".").pop();
      if (last === typed) return 3;
      if (last.startsWith(typed)) return 2;
      return full.includes(typed) ? 1 : 0;
    };
    return ranked
      .map((result, order) => ({ result, order, boost: titleMatch(result) }))
      .sort((a, b) => b.boost - a.boost || a.order - b.order)
      .slice(0, MAX_RESULTS)
      .map(({ result }) => result);
  }

  // Pages share titles across sections (a "Rewards" guide and API page), so
  // results name their section.
  const SECTION_LABELS = { use: "Guide", concepts: "Concept", develop: "Contributors", api: "API reference" };

  function resultMeta([docName, , , descr, , , kind]) {
    if (descr) return descr; // API objects: "Python class, in Rewards"
    const section = SECTION_LABELS[docName.split("/")[0]];
    const label = KIND_LABELS[kind] || "";
    return section ? `${label} · ${section}` : label;
  }

  function resultUrl(result) {
    const [docName, , anchor] = result;
    return new URL(`${docName}.html${anchor || ""}`, ROOT).href;
  }

  function setupLiveSearch(form) {
    const input = form.querySelector("input[name='q']");
    if (!input || form.dataset.liveSearch) return;
    form.dataset.liveSearch = "on";

    const panel = document.createElement("div");
    panel.className = "live-search";
    panel.hidden = true;
    const list = document.createElement("ul");
    list.className = "live-search-results";
    list.id = "live-search-results";
    list.setAttribute("role", "listbox");
    list.setAttribute("aria-label", "Search results");
    const status = document.createElement("p");
    status.className = "live-search-status";
    status.setAttribute("aria-live", "polite");
    panel.append(status, list);
    form.append(panel);

    input.setAttribute("role", "combobox");
    input.setAttribute("aria-autocomplete", "list");
    input.setAttribute("aria-controls", list.id);
    input.setAttribute("aria-expanded", "false");
    input.setAttribute("autocomplete", "off");

    let active = -1;
    let debounce = null;
    let latestQuery = "";

    const open = () => {
      if (!panel.hidden) return;
      panel.hidden = false;
      void panel.offsetWidth; // apply the closed style first so the fade-in runs
      panel.classList.add("is-open");
      input.setAttribute("aria-expanded", "true");
    };
    const close = () => {
      panel.classList.remove("is-open");
      panel.hidden = true;
      input.setAttribute("aria-expanded", "false");
      input.removeAttribute("aria-activedescendant");
      active = -1;
    };
    const options = () => Array.from(list.querySelectorAll("[role='option']"));
    const setActive = (index) => {
      const items = options();
      active = items.length ? (index + items.length) % items.length : -1;
      items.forEach((item, i) => item.setAttribute("aria-selected", String(i === active)));
      if (active >= 0) {
        input.setAttribute("aria-activedescendant", items[active].id);
        items[active].scrollIntoView({ block: "nearest" });
      } else {
        input.removeAttribute("aria-activedescendant");
      }
    };

    const render = (query, results) => {
      list.replaceChildren();
      active = -1;
      results.forEach((result, i) => {
        const [, title] = result;
        const item = document.createElement("li");
        const link = document.createElement("a");
        link.href = resultUrl(result);
        link.id = `live-search-option-${i}`;
        link.setAttribute("role", "option");
        link.setAttribute("aria-selected", "false");
        link.tabIndex = -1;
        const name = document.createElement("span");
        name.className = "live-search-title";
        name.textContent = title;
        const meta = document.createElement("span");
        meta.className = "live-search-meta";
        meta.textContent = resultMeta(result);
        link.append(name, meta);
        item.append(link);
        list.append(item);
      });
      const all = document.createElement("li");
      const allLink = document.createElement("a");
      allLink.className = "live-search-all";
      allLink.href = `${new URL("search.html", ROOT).href}?q=${encodeURIComponent(query)}`;
      allLink.id = `live-search-option-${results.length}`;
      allLink.setAttribute("role", "option");
      allLink.setAttribute("aria-selected", "false");
      allLink.tabIndex = -1;
      allLink.textContent = `All results for “${query}”`;
      all.append(allLink);
      list.append(all);
      status.textContent = results.length ? "" : `No quick matches for “${query}”.`;
    };

    const update = async () => {
      const query = input.value.trim();
      latestQuery = query;
      if (query.length < 2) {
        close();
        return;
      }
      if (!searchApi()?.hasIndex?.()) {
        status.textContent = "Loading search…";
        list.replaceChildren();
        open();
      }
      try {
        const api = await ensureSearch();
        if (query !== latestQuery) return; // the user kept typing
        render(query, runSearch(api, query));
        open();
      } catch {
        close(); // search engine unavailable; Enter still opens the search page
      }
    };

    input.addEventListener("focus", () => ensureSearch().catch(() => {}), { once: true });
    input.addEventListener("input", () => {
      clearTimeout(debounce);
      debounce = setTimeout(update, 80);
    });
    input.addEventListener("focus", () => {
      if (input.value.trim().length >= 2 && list.childElementCount) open();
    });
    input.addEventListener("keydown", (event) => {
      if (panel.hidden) return;
      if (event.key === "ArrowDown") {
        event.preventDefault();
        setActive(active + 1);
      } else if (event.key === "ArrowUp") {
        event.preventDefault();
        setActive(active - 1);
      } else if (event.key === "Enter" && active >= 0) {
        event.preventDefault();
        options()[active].click();
      } else if (event.key === "Escape") {
        event.preventDefault();
        close();
      }
    });
    // Keep focus in the box while clicking a result, then close after navigating.
    panel.addEventListener("pointerdown", (event) => event.preventDefault());
    panel.addEventListener("click", (event) => {
      if (event.target.closest("a")) {
        close();
        input.blur();
      }
    });
    document.addEventListener("pointerdown", (event) => {
      if (!form.contains(event.target)) close();
    });
    input.addEventListener("blur", () => setTimeout(() => {
      if (!form.contains(document.activeElement)) close();
    }, 0));
  }

  // ---------------------------------------------------------------------------
  // Start
  // ---------------------------------------------------------------------------
  function start() {
    setupContentsTracking();
    document.querySelectorAll("form.sidebar-search-container").forEach(setupLiveSearch);
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", start);
  else start();
})();
