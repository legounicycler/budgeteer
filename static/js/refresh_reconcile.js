// Formats a number into a string with a "$" and "-" if necessary
function balance_format(number) {
  if (number < 0) {
    text = '-$' + Math.abs(number).toFixed(2)
  } else {
    text = '$' + number.toFixed(2)
  }
  return text;
}

function text_to_num(txt) {
  num = parseFloat(txt.replace("$","")) //Remove the "$" character
  return num
}

function refresh_reconcile() {
  var page_total = text_to_num($("#page-total").text());
  var reconcile_balance = page_total;
  var pending_transactions = [];
  $("#transactions-bin .transaction-row").each(function() {
    if ($(this).hasClass("pending")) {
      //Add any pending transactions to an array to deal with after this loop
      pending_transactions.push($(this));
    } else {
      $balance = $(this).find(".balance");
      $reconcile_span = $(this).find(".reconcile-span");
      var amt = text_to_num($balance.text());
      if ($balance.hasClass("neutral")) {
        $reconcile_span.text(balance_format(reconcile_balance))
      } else {
        $reconcile_span.text(balance_format(reconcile_balance))
        reconcile_balance = reconcile_balance - amt
      }
    }
  });

  // If there are pending transactions, update their reconcile balances in reverse order
  var pending_reconcile_balance = page_total;
  pending_transactions.reverse().forEach(function($transaction_row) {
    $balance = $transaction_row.find(".balance");
    $reconcile_span = $transaction_row.find(".reconcile-span");
    var amt = text_to_num($balance.text());
    if ($balance.hasClass("neutral")) {
      $reconcile_span.text(balance_format(pending_reconcile_balance))
    } else {
      pending_reconcile_balance = pending_reconcile_balance + amt
      $reconcile_span.text(balance_format(pending_reconcile_balance))
    }
  });
  
}