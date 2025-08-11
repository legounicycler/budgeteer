window.Budgeteer = window.Budgeteer || {};
Budgeteer.previous_page = null; // Used to store the previous page before a search
Budgeteer.only_clear_searchfield = true; // If true, only clear the search field, if false, return to previous page after search
Budgeteer.current_search = null; // Used to store the current search term

$(document).ready(function() {

  $("#transaction-search-form").on("submit", function(e) {
    e.preventDefault();
    var url = $(this).attr('action');
    var method = $(this).attr('method');
    var searchTerm = $("#transaction-search").val().trim();

    $("#multi-select-icons").addClass("hide");

    Budgeteer.only_clear_searchfield = false;
    Budgeteer.current_search = searchTerm; // Store the current search term
    if (!searchTerm) return; //TODO: This line should change because in an advanced search you don't necessarily have to enter a search term, you can just search by date ranges, etc.
    if (Budgeteer.current_page != "Search Results") { //If you're entering a new search from a search page, update the previous and current page
      Budgeteer.previous_page = Budgeteer.current_page;
      Budgeteer.current_page = "Search Results";
    }

    $.ajax({
      url: url,
      method: method,
      data: $(this).serialize() + "&timestamp=" + gen_timestamp(),
    }).done(function(o) {
      if (o.error) {M.toast({html: o.error}); return;}
      $('#transactions-bin').replaceWith(o.transactions_html);
      if ($("#transactions-scroller").length !== 0) { new SimpleBar($("#transactions-scroller")[0]); }
      $('#current-page').text(o.current_page);
      $("#page-total").hide();
      $("#separator").hide();
      Budgeteer.none_checked = true;
    });

  });

  // Clear search field, and if you're on a search page then return to the previous page you started from
  // TODO: Make this clear every field in the advanced search bar too
  $("#close-search").on('mousedown', function() {
    $(this).fadeOut(200); // Fade out the close button
    Budgeteer.current_search = null; // Reset the global variable used to store the current search term
    
    // Clear all the fields in the advanced search bar
    $("#transaction-search-form").trigger("reset");

    // Reset all checkboxes to unchecked
    $('#search-envelopes, #search-accounts').each(function() {
      const $select = $(this);
      const $input = $select.siblings('input.select-dropdown');
      const $ul = $('#' + $input.attr('data-target'));
      $ul.find('input[type="checkbox"]').each(function() {
        if ($(this).prop('checked')) {
         $(this).parent().parent().parent().click(); //Click the li element to uncheck/unselect the checkbox
        }
      });

    });

    M.updateTextFields();

    if (Budgeteer.only_clear_searchfield) return;

    // Return to the page you were on before you started the search
    $.ajax({
      type: 'POST',
      url: '/api/reset-search',
      data: JSON.stringify({"previous_page": Budgeteer.previous_page, "timestamp": gen_timestamp()}),
      contentType: 'application/json'
    }).done(function(o) {
      if (o['error']) { M.toast({html: o['error']}); return; }
      $('#transactions-bin').replaceWith(o['transactions_html']);
      if ($("#transactions-scroller").length !== 0) { new SimpleBar($("#transactions-scroller")[0]) } //Re-initialize the transactions-scroller if the envelope has transactions
      $('#current-page').text(o['current_page']);
      $("#separator").show();
      $('#page-total').text(o['page_total']).show();
      refresh_reconcile();
      Budgeteer.none_checked = true;
      Budgeteer.only_clear_searchfield = true;
      $("#multi-select-icons").addClass("hide");
    });
  });

  // Event handlers for the #transaction-search input
  $('#transaction-search').on('input', function() {
      $('#close-search').toggle(!!$(this).val()); // Show/hide the #close-search icon based on if there's text
  }).on('blur', function() {
      $('#close-search').css("pointer-events", "none");
  }).on('focus', function() {
      $('#close-search').css("pointer-events", "auto");
  });

  // Show/hide the advanced search fields when the advanced search dropdown arrow is clicked
  $("#advanced-search-button").on('click', toggleAdvancedSearch).on('keydown', function(e) {
    if (e.key === "Enter") {
      toggleAdvancedSearch();
    }
  });

  Budgeteer.initializeSpecialSelects();

}); // End document ready

// Function for toggling the advanced search bar
function toggleAdvancedSearch() {
  if ($("#dashboard-header").hasClass("collapsed")) {
    // If the header is collapsed, expand it
    var currentDashHeight = $('#dashboard-header').height();
    var currentBinHeight = $("#bin").height();
    $('#dashboard-header').css('height', 'auto');
    var newDashHeight = $('#dashboard-header').height();
    $("#bin").css("height", "calc(100% - " + newDashHeight + "px)");
    var newBinHeight = $("#bin").height();
    $('#dashboard-header').height(currentDashHeight);
    $('#bin').height(currentBinHeight);
    $("#dashboard-header").animate({height: newDashHeight}, 200);
    $("#bin").animate({height: newBinHeight}, 200); // TODO: Possibly do a smooth animation on this as well
    $("#dashboard-header, #advanced-search-button").removeClass("collapsed").addClass("expanded");

    // Adjust the tabselect attribute for all the inputs to make them selectable
    $('#advanced-search-row input, #advanced-search-row button').each(function() {
      $(this).attr('tabindex', '0'); // Make them focusable
    });

  } else {
    // If the header is expanded, collapse it
    var currentBinHeight = $("#bin").height();
    $("#bin").css("height", "calc(100% - 90px)");
    var newBinHeight = $("#bin").height();
    $('#bin').height(currentBinHeight);
    $("#dashboard-header").animate({height: '90px'}, 200);
    $("#bin").animate({height: newBinHeight}, 200); // TODO: Possibly do a smooth animation on this as well
    $("#dashboard-header, #advanced-search-button").removeClass("expanded").addClass("collapsed");
  
    // Adjust the tabselect attribute for all the inputs to make them non-selectable
    $('#advanced-search-row input, #advanced-search-row button').each(function() {
      $(this).attr('tabindex', '-1'); // Make them non-focusable
    });
  }
}

// Function for initializing the special envelope/account select elements in the advanced-search row
Budgeteer.initializeSpecialSelects = function() {

  // 1. Initialize the selects (re-init safe)
  $('#search-envelopes, #search-accounts').formSelect({
    dropdownOptions: {
      container: '.content',
      onOpenStart: function(triggerEl) {
        // triggerEl is the input that launched the dropdown
        const $trigger = $(triggerEl);
        const ulId = $trigger.attr('data-target');
        const $ul = $('#' + ulId);
        if (!$ul.length) return;

        // Remove any prior key handlers (avoid duplicates if re-opened)
        $ul.off('.advKeys');

        // Get selectable items (exclude optgroup headers & disabled)
        const $items = $ul.find('li:not(.optgroup):not(.disabled)');
        if (!$items.length) return;

        // Make all items focusable (tabindex) so focus() works reliably
        $items.attr('tabindex', 0);

        // Clear previous "active/hovered" classes Materialize may have left
        $items.removeClass('active hovered');

        // Key handling inside dropdown list
        $ul.on('keydown.advKeys', function(e) {
          const $list = $(this);
            const $all = $list.find('li:not(.optgroup):not(.disabled)');
          if (!$all.length) return;

          // Determine current index (by active/hovered/focus)
          let idx = $all.index($all.filter('.active.hovered').first());
          if (idx < 0) idx = $all.index($all.filter('.active').first());
          if (idx < 0) idx = $all.index($all.filter(':focus').first());
          if (idx < 0) idx = 0;

          // Helper to update visual focus
          function setIndex(newIdx) {
            newIdx = Math.max(0, Math.min($all.length - 1, newIdx));
            $all.removeClass('active hovered');
            const $target = $all.eq(newIdx);
            $target.addClass('active hovered').focus();
          }

          // Navigation: Down / Up
          if (e.key === 'ArrowDown') {
            e.preventDefault(); e.stopImmediatePropagation();
            setIndex(idx + 1);
            return;
          } else if (e.key === 'ArrowUp') {
            e.preventDefault(); e.stopImmediatePropagation();
            setIndex(idx - 1);
            return;
          }

          // When enter key is pressed, select the dropdown item
          if (e.key === 'Enter') {
            e.preventDefault(); e.stopImmediatePropagation();
            const $targetLi = $all.eq(idx);
            // Simulate click which Materialize listens for
            $targetLi.trigger('mousedown').trigger('click');
            // Keep focus on same item for multi-select continued navigation
            setTimeout(() => $targetLi.focus(), 0);
            return;
          }

          // When Tab, Shift+Tab, Left, Right keys pressed, close dropdown and move to next/prev input
          if ((e.key === 'Tab' && !e.shiftKey) || e.key === 'ArrowRight') {
            e.preventDefault(); e.stopImmediatePropagation();
            focusSiblingInputFromDropdown($list, 'next');
            return;
          } else if ((e.key === 'Tab' && e.shiftKey) || e.key === 'ArrowLeft') {
            e.preventDefault(); e.stopImmediatePropagation();
            focusSiblingInputFromDropdown($list, 'prev');
            return;
          }

          // When escape key pressed, close dropdown, return focus to trigger element
          if (e.key === 'Escape') {
            closeDropdownReturnTrigger($list);
            return;
          }

        });
      }
    }
  });

  // 2.1 - Add custom style to dropdown to make envelope/account selections thinner/smaller
  // 2.2 - Override the onOpenEnd function for the select dropdown to manually set focus
  $('#search-envelopes, #search-accounts').each(function() {
    const $select = $(this);
    const $input = $select.siblings('input.select-dropdown');
    const $ul = $('#' + $input.attr('data-target'));

    // 2.1 - Add custom styles
    $ul.addClass('custom-dropdown-class');
    $input.attr('tabindex', '-1');

    // NEW: Track how the dropdown was opened
    $input.data('openByKeyboard', false);
    $input.on('keydown', function(e) {
      if (['Enter', 'ArrowDown'].includes(e.key)) {
        // Mark that the imminent open (triggered by this key) is keyboard initiated
        $input.data('openByKeyboard', true);
      }
    }).on('mousedown touchstart', function() {
      // Explicitly mark mouse/touch initiated open
      $input.data('openByKeyboard', false);
    });

    // 2.2 - Override the onOpenEnd dropdown function (conditionally apply custom focus)
    const selectEl = this;
    const fs = M.FormSelect.getInstance(selectEl);
    if (!fs || !fs.dropdown || fs._firstItemFocusPatched) return;

    const dd = fs.dropdown;
    const originalOnOpenEnd = dd.options.onOpenEnd; // Materialize's injected handler

    dd.options.onOpenEnd = function(el) {
      // Run original behavior first
      if (typeof originalOnOpenEnd === 'function') {
        originalOnOpenEnd.call(this, el);
      }

      // Only apply custom focus if opened via keyboard
      const openedByKeyboard = $input.data('openByKeyboard');
      // Reset flag for next time
      $input.data('openByKeyboard', false);
      if (!openedByKeyboard) return;

      // Custom focus logic (was always applied before; now conditional)
      const $ul = $(fs.dropdownOptions);
      const $items = $ul.find('li:not(.optgroup):not(.disabled)');
      if (!$items.length) return;

      $items.attr('tabindex', 0);
      $ul.find('li').removeClass('active hovered');

      const $first = $items.first().addClass('active hovered');
      fs.dropdown.focusedIndex = $first.index();
      $first[0].focus();
    };

    fs._firstItemFocusPatched = true;
  });

  // --- Helper Functions ---

  // Close dropdown & return focus to trigger input
  function closeDropdownReturnTrigger($ul) {
    const ulId = $ul.attr('id');
    const $trigger = $('input.select-dropdown[data-target="' + ulId + '"]');
    const selectEl = $trigger.siblings('select')[0];
    const fs = M.FormSelect.getInstance(selectEl);
    if (fs?.dropdown?.isOpen) fs.dropdown.close();
    $trigger.focus();
  }

  // Move focus to prev/next tabbable in advanced-search row
  function focusSiblingInputFromDropdown($ul, direction /* 'next' | 'prev' */) {
    const ulId = $ul.attr('id');
    const $trigger = $('input.select-dropdown[data-target="' + ulId + '"]');
    const selectEl = $trigger.siblings('select')[0];
    const fs = M.FormSelect.getInstance(selectEl);
    if (fs?.dropdown?.isOpen) fs.dropdown.close();

    focusSiblingInputFromTrigger($trigger, direction);
  }

  function focusSiblingInputFromTrigger($trigger, direction) {
    const $scope = $('#advanced-search-row');
    const $tabbables = $scope
      .find('input, select, button, textarea, a, [tabindex]:not([tabindex="-1"])')
      .filter(':visible:not([disabled])');
    const idx = $tabbables.index($trigger);
    if (idx < 0) return;
    const targetIdx = direction === 'prev'
      ? Math.max(0, idx - 1)
      : Math.min($tabbables.length - 1, idx + 1);
    $tabbables.eq(targetIdx).focus();
  }
};