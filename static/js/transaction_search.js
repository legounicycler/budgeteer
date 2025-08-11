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
    // TODO: Test if this works with #close-search.mousedown insteading of binding the event listener to the document
    $(document).on('mousedown', "#close-search", function() {
        $(this).fadeOut(200); // Fade out the close button
        Budgeteer.current_search = null; // Reset the global variable used to store the current search term
        $('#transaction-search').val(''); // Clear the search field
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

});
