// scrolling.js
// Unified custom scroll behavior (dropdowns + transaction scroller)
// Exposes Budgeteer.initScrollingBehavior()
(function(window, $){

  window.Budgeteer = window.Budgeteer || {};
  if (window.Budgeteer.initScrollingBehavior) {
    // Already defined (avoid duplicate listeners on hot reload)
    return;
  }

  window.Budgeteer.initScrollingBehavior = function initScrollingBehavior(){
    const DROPDOWN_SELECTOR = '.dropdown-content.select-dropdown:visible';
  const DEBUG = true; // set to false to silence logs
  function debug(){ if(!DEBUG) return; try { console.log('[scrolling]', ...arguments); } catch(_){} }

    function getContainingOpenDropdown(target) {
      const el = target.closest('.dropdown-content.select-dropdown');
      if (!el) return null;
      return $(el).is(':visible') ? el : null;
    }

    function isScrollable(el) { return el && el.scrollHeight > el.clientHeight + 1; }

    function closeDropdown($dd) {
      if (!$dd || !$dd.length) return;
      const id = $dd.attr('id');
      if (id) {
        const $trigger = $('input.select-dropdown[data-target="' + id + '"]');
        if ($trigger.length) { $trigger.dropdown('close'); return; }
      }
      $dd.hide();
    }

    function closeAllDropdowns(exceptEl = null) {
      $(DROPDOWN_SELECTOR).each(function(){
        if (exceptEl && this === exceptEl) return;
        closeDropdown($(this));
      });
    }

    function handleTransactionScrollerWheel(e, scrollerEl) {
      if (!scrollerEl) return;
      const deltaY = e.deltaY;
      const scrollTop = window.scrollY;
      const windowHeight = window.innerHeight;
      const documentHeight = Math.max(document.body.scrollHeight, document.documentElement.scrollHeight);

      const binScrollTop = scrollerEl.scrollTop;
      const binScrollHeight = scrollerEl.scrollHeight;
      const binClientHeight = scrollerEl.clientHeight;

      const atBottomOfPage = scrollTop + windowHeight >= documentHeight - 1;
      const atTopOfPage = scrollTop === 0;
      const atTopOfBin = binScrollTop === 0;
      const atBottomOfBin = binScrollTop + binClientHeight >= binScrollHeight - 1;

      // Middle of page: force page scroll only (ignore scroller native)
      if (!atTopOfPage && !atBottomOfPage) {
        debug('wheel: middle-of-page redirect to page', {deltaY});
        e.preventDefault();
        window.scrollBy(0, deltaY);
        return;
      }

      // At bottom or top of page: allow native scroller momentum if it can scroll in that direction.
      if (atBottomOfPage) {
        if ((deltaY > 0 && !atBottomOfBin) || (deltaY < 0 && !atTopOfBin)) {
          debug('wheel: at bottom-of-page letting scroller handle momentum', {deltaY});
          // Do NOT preventDefault or manually adjust scrollTop -> preserve momentum.
          return;
        }
      }
      // Upward momentum handoff: scroller top -> page (when user scrolls up and scroller can't scroll further)
      if (atTopOfBin && deltaY < 0 && !atTopOfPage) {
        debug('wheel: handoff scroller->page (up)', {deltaY});
        e.preventDefault(); // prevent scroller bounce
        window.scrollBy(0, deltaY); // apply remaining momentum to page
        return;
      }
      // Otherwise fall through to native behavior.
    }

    function handleDropdownWheel(e, dropdownEl) {
      const deltaY = e.deltaY;
      if (isScrollable(dropdownEl)) {
        dropdownEl.scrollTop += deltaY; e.preventDefault(); e.stopPropagation();
      } else {
        closeDropdown($(dropdownEl));
      }
    }

    function onWheel(e) {
      if (window.Budgeteer && window.Budgeteer.longPressSelecting) {
        // During drag-select, let native scroller/page behavior occur (don't hijack)
        return;
      }
      const target = e.target;
      const dropdownEl = getContainingOpenDropdown(target);
      if (dropdownEl) { debug('wheel: inside dropdown'); handleDropdownWheel(e, dropdownEl); return; }

      if ($(DROPDOWN_SELECTOR).length) { debug('wheel: closing stray dropdowns'); closeAllDropdowns(); }

      const scrollerEl = window.Budgeteer.transactionsScrollerElement;
      if (scrollerEl && (target === scrollerEl || scrollerEl.contains(target))) {
        debug('wheel: over scroller');
        handleTransactionScrollerWheel(e, scrollerEl); return; }

      // Momentum handoff only (page -> scroller) when page bottom & scrolling down & scroller not at bottom
      if (scrollerEl && e.deltaY > 0) {
        const scrollTop = window.scrollY;
        const windowHeight = window.innerHeight;
        const documentHeight = Math.max(document.body.scrollHeight, document.documentElement.scrollHeight);
        const atBottomOfPage = scrollTop + windowHeight >= documentHeight - 1;
        if (atBottomOfPage) {
          const binScrollTop = scrollerEl.scrollTop;
          const binScrollHeight = scrollerEl.scrollHeight;
          const binClientHeight = scrollerEl.clientHeight;
          const atBottomOfBin = binScrollTop + binClientHeight >= binScrollHeight - 1;
          if (!atBottomOfBin) { debug('wheel: momentum handoff page->scroller', {deltaY: e.deltaY}); scrollerEl.scrollTop += e.deltaY; e.preventDefault(); return; }
        }
      }
    }

    let activeDropdownTouch = null; let lastTouchY = null;
    function onTouchStart(e){
      if (window.Budgeteer && window.Budgeteer.longPressSelecting) return; // selection will manage its own prevention
      const target = e.target; const dropdownEl = getContainingOpenDropdown(target);
      activeDropdownTouch = dropdownEl ? dropdownEl : null;
      lastTouchY = e.touches[0].clientY; // always capture starting Y for momentum calculations
    }
    function onTouchMove(e){
      if (window.Budgeteer && window.Budgeteer.longPressSelecting) {
        // Don't modify scroll while user is drag selecting; selection code handles preventDefault
        return;
      }
      const currentY = e.touches[0].clientY;
      const deltaY = (lastTouchY !== null) ? (lastTouchY - currentY) : 0; // positive -> user moves finger up (content should scroll down)
      lastTouchY = currentY;

      if (Math.abs(deltaY) < 0.5) return; // ignore jitter early for performance

      // Dropdown handling
      if (activeDropdownTouch){
        if (isScrollable(activeDropdownTouch)){
          activeDropdownTouch.scrollTop += deltaY; e.preventDefault(); e.stopPropagation(); debug('touch: scrolling dropdown', {deltaY});
        } else {
          debug('touch: closing non-scrollable dropdown');
          closeDropdown($(activeDropdownTouch)); activeDropdownTouch = null; // allow page scroll
        }
        return;
      }

      // Close any open dropdowns if finger moves outside
      if ($(DROPDOWN_SELECTOR).length) { debug('touch: closing stray dropdowns'); closeAllDropdowns(); }

      const target = e.target; const scrollerEl = window.Budgeteer.transactionsScrollerElement;
      if (!scrollerEl) return;

      // Finger over scroller -> mimic wheel logic minimally (only middle-of-page redirect)
      if (target === scrollerEl || scrollerEl.contains(target)) {
        const scrollTop = window.scrollY;
        const windowHeight = window.innerHeight;
        const documentHeight = Math.max(document.body.scrollHeight, document.documentElement.scrollHeight);
        const atBottomOfPage = scrollTop + windowHeight >= documentHeight - 1;
        const atTopOfPage = scrollTop === 0;
        const binScrollTop = scrollerEl.scrollTop;
        const binClientHeight = scrollerEl.clientHeight;
        const binScrollHeight = scrollerEl.scrollHeight;
        const atTopOfBin = binScrollTop === 0;
        const atBottomOfBin = binScrollTop + binClientHeight >= binScrollHeight - 1;
        if (!atBottomOfPage && !atTopOfPage) {
          debug('touch: middle-of-page redirect to page', {deltaY});
          e.preventDefault();
          window.scrollBy(0, deltaY);
        } else {
          // allow native scroller momentum
          debug('touch: native scroller momentum', {deltaY});
          // Upward handoff when scroller at top but page can scroll
          if (atTopOfBin && deltaY < 0 && !atTopOfPage) {
            debug('touch: handoff scroller->page (up)', {deltaY});
            e.preventDefault();
            window.scrollBy(0, deltaY);
          }
        }
        return;
      }

      // Momentum handoff page->scroller when reaching bottom and scrolling down (deltaY>0 means content moves down)
      if (deltaY > 0) {
        const scrollTop = window.scrollY;
        const windowHeight = window.innerHeight;
        const documentHeight = Math.max(document.body.scrollHeight, document.documentElement.scrollHeight);
        const atBottomOfPage = scrollTop + windowHeight >= documentHeight - 1;
        if (atBottomOfPage) {
          const binScrollTop = scrollerEl.scrollTop;
          const binScrollHeight = scrollerEl.scrollHeight;
          const binClientHeight = scrollerEl.clientHeight;
            const atBottomOfBin = binScrollTop + binClientHeight >= binScrollHeight - 1;
          if (!atBottomOfBin) {
            debug('touch: momentum handoff page->scroller', {deltaY});
            scrollerEl.scrollTop += deltaY;
            e.preventDefault();
            return;
          }
        }
      }
      // otherwise native page scroll
    }
    function onTouchEnd(){ activeDropdownTouch = null; lastTouchY = null; }

    // Remove legacy listeners first
    document.removeEventListener('wheel', onWheel, { capture: true });
    document.removeEventListener('touchstart', onTouchStart, { capture: true });
    document.removeEventListener('touchmove', onTouchMove, { capture: true });

    document.addEventListener('wheel', onWheel, { passive: false, capture: true });
    document.addEventListener('touchstart', onTouchStart, { passive: true, capture: true });
    document.addEventListener('touchmove', onTouchMove, { passive: false, capture: true });
    document.addEventListener('touchend', onTouchEnd, { passive: true, capture: true });
    document.addEventListener('touchcancel', onTouchEnd, { passive: true, capture: true });
  };

})(window, jQuery);
