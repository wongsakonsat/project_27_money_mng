/**
 * Google Apps Script for Money Management Backend
 * Instructions:
 * 1. Open your Google Sheet
 * 2. Click "Extensions" -> "Apps Script" (ส่วนขยาย -> Apps Script)
 * 3. Paste this entire code, click Save
 * 4. Click "Deploy" (การทำให้ใช้งานได้) -> "New deployment" (การทำให้ใช้งานได้รายการใหม่)
 * 5. Select Type: "Web app" (เว็บแอป)
 * 6. Set "Execute as": "Me" (ฉัน)
 * 7. Set "Who has access": "Anyone" (ทุกคน)
 * 8. Click "Deploy" and Copy the Web App URL into your Streamlit App!
 */

function doGet(e) {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  ensureSheets(ss);
  
  var accounts = getSheetData(ss.getSheetByName("Accounts"));
  var transactions = getSheetData(ss.getSheetByName("Transactions"));
  var wishlist = getSheetData(ss.getSheetByName("Wishlist"));
  
  var payload = {
    status: "success",
    accounts: accounts,
    transactions: transactions,
    wishlist: wishlist,
    synced_at: new Date().toISOString()
  };
  
  return ContentService.createTextOutput(JSON.stringify(payload))
    .setMimeType(ContentService.MimeType.JSON);
}

function doPost(e) {
  try {
    var ss = SpreadsheetApp.getActiveSpreadsheet();
    ensureSheets(ss);
    var data = JSON.parse(e.postData.contents);
    
    if (data.action === "add_transaction") {
      var tx = data.transaction;
      var ws = ss.getSheetByName("Transactions");
      ws.appendRow([
        tx.Transaction_ID,
        tx.Date,
        tx.Cycle,
        tx.Type,
        tx.From_Account,
        tx.To_Account,
        tx.Category,
        tx.Amount,
        tx.Note
      ]);
      return ContentService.createTextOutput(JSON.stringify({status: "success", message: "Transaction added"}))
        .setMimeType(ContentService.MimeType.JSON);
    }
    
    if (data.action === "sync_all") {
      if (data.accounts) setSheetData(ss.getSheetByName("Accounts"), data.accounts);
      if (data.transactions) setSheetData(ss.getSheetByName("Transactions"), data.transactions);
      if (data.wishlist) setSheetData(ss.getSheetByName("Wishlist"), data.wishlist);
      
      return ContentService.createTextOutput(JSON.stringify({status: "success", message: "All synced successfully"}))
        .setMimeType(ContentService.MimeType.JSON);
    }
    
    return ContentService.createTextOutput(JSON.stringify({status: "error", message: "Unknown action"}))
      .setMimeType(ContentService.MimeType.JSON);
  } catch (err) {
    return ContentService.createTextOutput(JSON.stringify({status: "error", message: err.toString()}))
      .setMimeType(ContentService.MimeType.JSON);
  }
}

function ensureSheets(ss) {
  var required = {
    "Accounts": ["Account_Name", "Initial_Balance", "Current_Balance", "Updated_At"],
    "Transactions": ["Transaction_ID", "Date", "Cycle", "Type", "From_Account", "To_Account", "Category", "Amount", "Note"],
    "Wishlist": ["Item_Name", "Target_Price", "Target_Month", "Priority", "Status", "Current_Saved"]
  };
  
  for (var name in required) {
    var sheet = ss.getSheetByName(name);
    if (!sheet) {
      sheet = ss.insertSheet(name);
      sheet.appendRow(required[name]);
    }
  }
}

function getSheetData(sheet) {
  var data = sheet.getDataRange().getValues();
  if (data.length <= 1) return [];
  var headers = data[0];
  var rows = [];
  for (var i = 1; i < data.length; i++) {
    var obj = {};
    for (var j = 0; j < headers.length; j++) {
      obj[headers[j]] = data[i][j];
    }
    rows.push(obj);
  }
  return rows;
}

function setSheetData(sheet, items) {
  if (!items || items.length === 0) return;
  var headers = Object.keys(items[0]);
  sheet.clearContents();
  var matrix = [headers];
  for (var i = 0; i < items.length; i++) {
    var row = [];
    for (var j = 0; j < headers.length; j++) {
      row.push(items[i][headers[j]]);
    }
    matrix.push(row);
  }
  sheet.getRange(1, 1, matrix.length, headers.length).setValues(matrix);
}
