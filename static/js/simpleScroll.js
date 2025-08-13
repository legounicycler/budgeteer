// simpleScroll.js
// Lightweight unified scroll behavior for Materialize select dropdowns.
// Implements ONLY the three requested rules (wheel + touch):
// 1. Scroll outside a select dropdown -> close it (if any open) and let page scroll.
// 2a. Scroll inside a scrollable dropdown -> consume and scroll only that dropdown (page locked for that event).
// 2b. Scroll inside a non‑scrollable dropdown -> close it and allow page scroll to continue.
//
// PERFORMANCE OPTIMIZATIONS (compared to prior version):
// - Avoids expensive jQuery ":visible" queries on every wheel/touch event.
// - Caches the last open dropdown element (lastOpenDropdown) and only re-queries when needed.
// - Uses cheap property checks (offsetParent) to test visibility instead of jQuery :visible.
// - Minimizes DOM traversal: ancestor walk stops as soon as a dropdown is found.
// - No references to long-press / swipe selection flags (requirements update) and does not preventDefault
//   unless strictly necessary (inside scrollable dropdown), reducing main thread work.
//
// ASSUMPTIONS / TRADE-OFFS:
// - Typically only one dropdown is open at a time in Materialize; we track just the last one.
// - If multiple were somehow forced open, outside scroll would only auto-close the last interacted one.
//   (This is acceptable given normal library behavior.)
// - We retain minimal jQuery usage ONLY for invoking Materialize's dropdown('close') API.
//
// INTEGRATION:
// - Exposed via Budgeteer.initScrollingBehavior() which remains idempotent.
// - Attach listeners in capture phase so we can optionally cancel before page scroll.

(function() {
  // Ensure global namespace
  window.Budgeteer = window.Budgeteer || {};
  const DEBUG = true;

  // Public initializer (idempotent)
  Budgeteer.initScrollingBehavior = function initScrollingBehavior() {
    if (initScrollingBehavior._initialized) return; // idempotency guard
    initScrollingBehavior._initialized = true;

    // We track only the last open dropdown (DOM node)
    let lastOpenDropdown = null;

    // --- NEW: Fallback finder for a visible (open) select dropdown when cache is empty/stale.
    function getAnyVisibleDropdown() {
      const list = document.querySelectorAll('.dropdown-content.select-dropdown');
      for (let i = 0; i < list.length; i++) {
        const el = list[i];
        if (el.offsetParent) return el;
      }
      return null;
    }

    // ------------- Helper Functions -------------

    function getOpenDropdownAncestor(node) {
      // Walk up ancestor chain looking for a dropdown-content.select-dropdown element.
      while (node && node !== document) {
        if (node.classList && node.classList.contains('dropdown-content') && node.classList.contains('select-dropdown')) {
          // Treat as open if it's currently rendered (offsetParent != null covers display:none or detached cases)
          return node.offsetParent ? node : null;
        }
        node = node.parentNode;
      }
      return null;
    }

    function isScrollable(el) {
      return el && el.scrollHeight > el.clientHeight + 1; // small buffer for fractional pixels
    }

    function closeDropdown($dropdown) {
      if (!$dropdown || !$dropdown.length) return;
      const id = $dropdown.attr('id');
      if (id) {
        const $trigger = $('input.select-dropdown[data-target="' + id + '"]');
        if ($trigger.length) {
          $trigger.dropdown('close');
          return;
        }
      }
      // Fallback: hide (should rarely happen if Materialize API is present)
      $dropdown.hide();
    }

    function closeTrackedDropdown(exceptNode = null) {
      // Refresh stale cache
      console.log('closeTrackedDropdown', { lastOpenDropdown, exceptNode });
      if (lastOpenDropdown && !isVisible(lastOpenDropdown)) lastOpenDropdown = null;

      // If no cached dropdown, attempt discovery (cheap, infrequent path)
      if (!lastOpenDropdown) {
        lastOpenDropdown = getAnyVisibleDropdown();
      }

      if (!lastOpenDropdown) return;
      if (exceptNode && lastOpenDropdown === exceptNode) return;

      
      closeDropdown($(lastOpenDropdown));
      lastOpenDropdown = null;
    }

    function isVisible(el) {
      return !!(el && el.offsetParent);
    }

    // --- NEW: Track when a dropdown is about to open (click/focus on trigger).
    function rememberDropdownFromTrigger(trigger) {
      if (!trigger) return;
      const id = trigger.getAttribute('data-target');
      if (!id) return;
      // Defer so Materialize has time to insert/show the dropdown.
      setTimeout(() => {
        const el = document.getElementById(id);
        if (el && el.offsetParent) lastOpenDropdown = el;
      }, 0);
    }

    function onPossibleOpenEvent(e) {
      const trigger = e.target && e.target.closest && e.target.closest('input.select-dropdown');
      if (trigger) rememberDropdownFromTrigger(trigger);
    }

    // ------------- Wheel Handling -------------

    function onWheel(e) {
      const dropdownEl = getOpenDropdownAncestor(e.target);
      // if (DEBUG) console.log('[scrolling] onWheel', { target: e.target, dropdown: dropdownEl, isScrollable: isScrollable(dropdownEl) });
      if (dropdownEl) {
        // Update cache
        lastOpenDropdown = dropdownEl;
        if (isScrollable(dropdownEl)) {
          // Rule 2a
            dropdownEl.scrollTop += e.deltaY;
          e.preventDefault();
          e.stopPropagation();
        } else {
          // Rule 2b
          closeTrackedDropdown(); // closes only if different (guard inside)
          // Let page scroll
        }
        return; // Done handling
      }

      // Outside any dropdown
      closeTrackedDropdown(); // Rule 1 (will no-op if none)
      // Let native page scroll proceed
    }

  // ------------- Touch Handling -------------
  // Mirrors wheel logic for scroll gestures. We purposely avoid referencing
  // any long-press / drag-selection flags (per updated requirements).

    let activeDropdownTouch = null; // DOM node of dropdown capturing touch scroll
    let lastTouchY = 0;

    function onTouchStart(e) {
      const dropdownEl = getOpenDropdownAncestor(e.target);
      activeDropdownTouch = dropdownEl;
      if (dropdownEl) {
        lastTouchY = e.touches[0].clientY;
      } else {
        // Outside dropdown -> will close on move (first scroll intent)
        lastTouchY = 0;
      }
    }

    function onTouchMove(e) {
      if (activeDropdownTouch) {
        const currentY = e.touches[0].clientY;
        const deltaY = lastTouchY - currentY; // mimic wheel sign
        lastTouchY = currentY;
        if (isScrollable(activeDropdownTouch)) {
          activeDropdownTouch.scrollTop += deltaY;
          e.preventDefault(); // keep page from moving
          e.stopPropagation();
        } else {
          // Non-scrollable: close then allow page scroll
      closeDropdown($(activeDropdownTouch));
          activeDropdownTouch = null;
          // Do not preventDefault so page scroll can begin
        }
        return;
      }

    // Moving outside any dropdown -> close cached (rule 1)
    closeTrackedDropdown();
      // Native page scroll
    }

    function onTouchEnd() {
      activeDropdownTouch = null;
      lastTouchY = 0;
    }

    // ------------- Attach Listeners -------------
    document.addEventListener('wheel', onWheel, { passive: false, capture: true });
    document.addEventListener('touchstart', onTouchStart, { passive: true, capture: true });
    document.addEventListener('touchmove', onTouchMove, { passive: false, capture: true });
    document.addEventListener('touchend', onTouchEnd, { passive: true, capture: true });
    document.addEventListener('touchcancel', onTouchEnd, { passive: true, capture: true });

    // --- NEW: Capture click & focusin to cache newly opened dropdowns early.
    document.addEventListener('click', onPossibleOpenEvent, true);
    document.addEventListener('focusin', onPossibleOpenEvent, true);
  };
})();
