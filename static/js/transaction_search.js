window.Budgeteer = window.Budgeteer || {};
Budgeteer.previous_page = null; // Used to store the previous page before a search
Budgeteer.only_clear_searchfield = true; // If true, only clear the search field, if false, return to previous page after search
Budgeteer.current_search = null; // Used to store the current search term

$(document).ready(function() {

    $("#transaction-search-form").on("submit", function(e) {
        console.log("Transaction search form submitted");
        e.preventDefault();
        var url = $(this).attr('action');
        var method = $(this).attr('method');
        Budgeteer.only_clear_searchfield = false;
        var searchTerm = $("#transaction-search").val().trim();
        Budgeteer.current_search = searchTerm; // Store the current search term
        if (!searchTerm) return; //TODO: This line should change because in an advanced search you don't necessarily have to enter a search term, you can just search by date ranges, etc.
        $("#multi-select-icons").addClass("hide");
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
        $("#transaction-search-form").trigger("reset"); // Clear the search fields
        M.updateTextFields();
        if (Budgeteer.only_clear_searchfield) {
            return;
        } else {
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
        }
    });

    // Event handlers for the #transaction-search input
    $('#transaction-search').on('input', function() {
        $('#close-search').toggle(!!$(this).val()); // Show/hide the #close-search icon based on if there's text
    }).on('blur', function() {
        $('#close-search').css("pointer-events", "none");
    }).on('focus', function() {
        $('#close-search').css("pointer-events", "auto");
    });

    // TODO: Investigate if the collapsed and expanded classes are needed anymore
    $("#advanced-search-button").on('click', function() {
        if ($("#dashboard-header").hasClass("collapsed")) {
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
        } else {
            var currentBinHeight = $("#bin").height();
            $("#bin").css("height", "calc(100% - 90px)");
            var newBinHeight = $("#bin").height();
            $('#bin').height(currentBinHeight);
            $("#dashboard-header").animate({height: '90px'}, 200);
            $("#bin").animate({height: newBinHeight}, 200); // TODO: Possibly do a smooth animation on this as well
            $("#dashboard-header, #advanced-search-button").removeClass("expanded").addClass("collapsed");
        }
        
    });



    // Initialize the special multi-selects (advanced search)
    $('#search-envelopes, #search-accounts').formSelect({
      dropdownOptions: {
        container: '.content',
        onOpenEnd: function(ulEl) {
          const $ul = $(ulEl);
          const $items = $ul.find('li:not(.disabled)');
          // Make items focusable and sync both classes Materialize may use
          $items.attr('tabindex', 0);
          $items.removeClass('active hovered');
          const $first = $items.first();
          // Defer to run after Materialize finishes its own open handlers
          setTimeout(() => {
            $first.addClass('active hovered').focus();
          }, 0);
        }
      }
    });

    // Open on Enter only and focus the first option
    $('#search-envelopes, #search-accounts')
      .siblings('input.select-dropdown')
      .off('.advOpen')
      .on('keydown.advOpen', function(e) {
        if (e.key === 'Enter') {
          e.preventDefault();
          e.stopImmediatePropagation();
          const $trigger = $(this);
          const ulId = $trigger.attr('data-target');
          const $ul = $('#' + ulId);
          const selectEl = $trigger.siblings('select')[0];
          const fs = M.FormSelect.getInstance(selectEl);
          if (fs && fs.dropdown && !fs.dropdown.isOpen) fs.dropdown.open();

          // Focus first option after open
          setTimeout(() => {
            const $items = $ul.find('li:not(.disabled)');
            if ($items.length) {
              $items.attr('tabindex', 0).removeClass('active hovered');
              $items.first().addClass('active hovered').focus();
            }
          }, 0);
        }
      });

    // Helper: move focus to prev/next tabbable in advanced-search row
    function focusSiblingInputFromDropdown($ul, direction /* 'next' | 'prev' */) {
      const ulId = $ul.attr('id');
      const $trigger = $('input.select-dropdown[data-target="' + ulId + '"]');
      const selectEl = $trigger.siblings('select')[0];
      const fs = M.FormSelect.getInstance(selectEl);
      if (fs?.dropdown?.isOpen) fs.dropdown.close();

      const $scope = $('#advanced-search-row');
      const $tabbables = $scope
        .find('input, select, button, textarea, a, [tabindex]:not([tabindex="-1"])')
        .filter(':visible:not([disabled])');

      const idx = $tabbables.index($trigger);
      const targetIdx = direction === 'prev' ? Math.max(0, idx - 1) : Math.min($tabbables.length - 1, idx + 1);
      $tabbables.eq(targetIdx).focus();
    }

    // Key handling while dropdown UL is open (only these two selects)
    $('#search-envelopes, #search-accounts').each(function() {
      const $input = $(this).siblings('input.select-dropdown');
      const $ul = $('#' + $input.attr('data-target'));

      $ul.off('.advKeys').on('keydown.advKeys', function(e) {
        const $list = $(this);
        const $items = $list.find('li:not(.disabled)');
        // Derive current index from classes or focus
        let idx = $items.index($items.filter('.active.hovered').first());
        if (idx < 0) idx = $items.index($items.filter('.active').first());
        if (idx < 0) idx = $items.index($items.filter(':focus').first());
        if (idx < 0) idx = 0;

        // Tab / Shift+Tab or Left/Right: close and move focus
        if (e.key === 'Tab') {
          e.preventDefault(); e.stopImmediatePropagation();
          focusSiblingInputFromDropdown($list, e.shiftKey ? 'prev' : 'next');
          return;
        }
        if (e.key === 'ArrowLeft') {
          e.preventDefault(); e.stopImmediatePropagation();
          focusSiblingInputFromDropdown($list, 'prev');
          return;
        }
        if (e.key === 'ArrowRight') {
          e.preventDefault(); e.stopImmediatePropagation();
          focusSiblingInputFromDropdown($list, 'next');
          return;
        }

        // Navigate options (override Materialize handlers)
        if (e.key === 'ArrowDown') {
          e.preventDefault(); e.stopImmediatePropagation();
          if ($items.length) {
            $items.removeClass('active hovered');
            idx = Math.min($items.length - 1, idx + 1);
            $items.eq(idx).addClass('active hovered').focus();
          }
          return;
        }
        if (e.key === 'ArrowUp') {
          e.preventDefault(); e.stopImmediatePropagation();
          if ($items.length) {
            $items.removeClass('active hovered');
            idx = Math.max(0, idx - 1);
            $items.eq(idx).addClass('active hovered').focus();
          }
          return;
        }

        // Select/toggle current option explicitly to avoid “one behind”
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault(); e.stopImmediatePropagation();
          const $targetLi = $items.eq(idx);
          // Trigger Materialize selection
          // (click is what FormSelect listens to on li/span)
          $targetLi.trigger('mousedown').trigger('click');
          return;
        }
      });
    });


});
