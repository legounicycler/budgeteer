window.Budgeteer = window.Budgeteer || {};
Budgeteer.previous_page = null; // Used to store the previous page before a search
Budgeteer.only_clear_searchfield = true; // If true, only clear the search field, if false, return to previous page after search
Budgeteer.current_search = null; // Used to store the current search term

$(document).ready(function() {


    $('#transaction-search').on('input', function() {
        // Show/hide the #close-search icon based on if there's text
        $('#close-search').toggle(!!$(this).val());
    });

    // Clear search and restore original page using the existing #close-search
    $(document).on('mousedown', "#close-search", function() {
        $(this).fadeOut(200);
        Budgeteer.current_search = null; // Reset the current search term
        if (Budgeteer.only_clear_searchfield) {
            $('#transaction-search').val('');
            return;
        } else {
            $('#transaction-search').val('');
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

    $('#transaction-search').keypress(function(e) {
        if (e.key === "Enter") {
            e.preventDefault();
            Budgeteer.only_clear_searchfield = false;
            var searchTerm = $(this).val().trim();
            Budgeteer.current_search = searchTerm; // Store the current search term
            if (!searchTerm) return;
            $("#multi-select-icons").addClass("hide");
            if (Budgeteer.current_page != "Search Results") {
                Budgeteer.previous_page = Budgeteer.current_page;
                Budgeteer.current_page = "Search Results";
            }
            $.ajax({
                type: 'POST',
                url: '/api/search-transactions',
                data: JSON.stringify({'search_term': searchTerm, "timestamp": gen_timestamp()}),
                contentType: 'application/json'
            }).done(function(o) {
                if (o.error) {M.toast({html: o.error}); return;}
                $('#transactions-bin').replaceWith(o.transactions_html);
                if ($("#transactions-scroller").length !== 0) { new SimpleBar($("#transactions-scroller")[0]); }
                $('#current-page').text(o.current_page);
                $("#page-total").hide();
                $("#separator").hide();
                Budgeteer.none_checked = true;
            });
        }
    });

    $('#transaction-search').on('blur', function() {
        $('#close-search').css("pointer-events", "none");
    }).on('focus', function() {
        $('#close-search').css("pointer-events", "auto");
    });

    $("#advanced-search-button").on('click', function() {
        if ($("#dashboard-header").hasClass("collapsed")) {
            console.log("HAS CLASS collapsed");
            $("#dashboard-header").animate({height: '180px'}, 200);
            $("#advanced-search-button").animate()
            // $("#dashboard-title-and-search-row").animate({height: '50%'}, 170);
            $("#dashboard-header, #dashboard-title-and-search-row, #advanced-search-button").removeClass("collapsed");
            $("#dashboard-header, #dashboard-title-and-search-row, #advanced-search-button").addClass("expanded");
        } else {
            console.log("DOES NOT HAVE CLASS collapsed");
            $("#dashboard-header").animate({height: '90px'}, 200);
            // $("#dashboard-title-and-search-row").animate({height: '100%'}, 200);
            $("#dashboard-header, #dashboard-title-and-search-row, #advanced-search-button").addClass("collapsed");
            $("#dashboard-header, #dashboard-title-and-search-row, #advanced-search-button").removeClass("expanded");
            // $("#advanced-search-row").addClass("hide");
        }
        
    });

});
