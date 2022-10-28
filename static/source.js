
// Set the current date as the max allowed date in creation forms.
let today = new Date()
let dd = String(today.getDate()).padStart(2, '0');
let mm = String(today.getMonth() + 1).padStart(2, '0');
let yyyy = today.getFullYear();
today = yyyy + '-' + mm + '-' + dd;
currentDate = document.querySelector('#current_date');
currentDate.setAttribute('max', today);
currentDate.setAttribute('value', today);


function newLine(){
    // Get the last quote_line
    let lastQuoteLine = document.getElementById('quote_lines').lastElementChild;
    // Get the last quote_line id and store it in a variable
    let lastQuoteLineId = lastQuoteLine.getAttribute('id');
    // Get the id_index by accessing the last 2 characters of the id
    let lastIdIndex = lastQuoteLineId.substring(5, 7);
    // Increment the id_index by 1 for the new row
    let newIdIndex = parseInt(lastIdIndex, 10) + 1;
    newIdIndex = newIdIndex.toString().padStart(2, "0");
    // Form the new ids strings with element name + the new index
    let newQuoteLineId = "line_" + newIdIndex
    let newLineItemElementId = "item_" + newIdIndex
    
    // Get the template row
    let templateRow = document.getElementById('template_row');
    // Clone the row and store it in a variable
    let newQuoteLine = templateRow.cloneNode(true);
    // Remove the hidden attribute to the new row
    newQuoteLine.removeAttribute('hidden');

    // Set the id for the new line <tr>
    newQuoteLine.id = newQuoteLineId;
    // Get the last element child of the new line
    let newLineLastElement = newQuoteLine.lastElementChild;
    // Change the value of the "onclick" attribute to pass the current id to the function 
    onclickValue = "removeLine('" + newQuoteLineId + "')"
    newLineLastElement.setAttribute("onclick", onclickValue)
    // Get the "item" element of the new_line
    let newLineFirstElement = newQuoteLine.firstElementChild;
    let newLineItemElement = newLineFirstElement.nextElementSibling;
    // Set a new Id for the new ItemElement
    newLineItemElement.id = newLineItemElementId;
    // Get the input element inside the item element
    let inputOfItemElement = newLineItemElement.firstElementChild;
    // Change the value of the oninput attribute to include the current itemElementId
    onInputValue = "getItem('" + newLineItemElementId + "')";
    inputOfItemElement.setAttribute('oninput', onInputValue);
    // Get the quantity element
    let newDescriptionElement = newLineItemElement.nextElementSibling;
    let newQuantityElement = newDescriptionElement.nextElementSibling;
    // Get to the quantity child input and change the "onchange" attribute
    let inputOfQuantityElement = newQuantityElement.firstElementChild;
    quantityOnChangeValue = "calculateTotal('" + newQuoteLineId + "')";
    inputOfQuantityElement.setAttribute('onchange', quantityOnChangeValue);
    // Get the list_price element
    let newListPriceElement = newQuantityElement.nextElementSibling;
    // Get to the list_price child input element and change the "onchange" attribute
    let inputOfListPriceElement = newListPriceElement.firstElementChild;
    priceOnChangeValue = "calculateNetPriceAndTotal('" + newQuoteLineId + "')";
    inputOfListPriceElement.setAttribute('onchange', priceOnChangeValue);
    // Get the discount element
    let newDiscountElement = newListPriceElement.nextElementSibling;
    // Get the child input of the discount element and change its "onchage attribute"
    let inputOfDiscountElement = newDiscountElement.firstElementChild;
    inputOfDiscountElement.setAttribute('onchange', priceOnChangeValue);


    // Append the new line to the DOM
    document.querySelector('#quote_lines').appendChild(newQuoteLine);
};



function removeLine(lineId){
    // Check the line to remove is not the last one standing
    if(document.getElementById(lineId)!=document.getElementById('quote_lines').firstElementChild || 
    document.getElementById(lineId)!=document.getElementById('quote_lines').lastElementChild) {
        let lineToRemove = document.getElementById(lineId);
        lineToRemove.remove();

        // This section will update grand totals
        let totals = document.getElementsByClassName('total');
        // Get the total net value
        let totalNetValue = 0;
        for(let i = 0; i < totals.length; i++){
            totalNetValue += parseFloat(totals[i].value);
        }
        // Get the total tax amount
        let taxAmount = Math.round(((totalNetValue * 0.18) + Number.EPSILON) * 100) / 100; // hard coded
        // Get the total tax included
        let totalTaxIncluded = totalNetValue + taxAmount;
        // Update all the values in the respective elements
        let totalNetValueElement = document.getElementById('total_net_value');
        totalNetValueElement.setAttribute('value', totalNetValue);
        let TaxAmountElement = document.getElementById('tax_amount');
        TaxAmountElement.setAttribute('value', taxAmount);
        let totalTaxIncludedElement = document.getElementById('total_tax_included');
        totalTaxIncludedElement.setAttribute('value', totalTaxIncluded);
    }
    else{
        alert("You can't remove all the lines");
    }
};



// Check customer_id and bring company name
let customerId = document.getElementById('customer_id')
customerId.addEventListener('input', async function (){
    let response = await fetch('/customers/' + customerId.value);
    let customer = await response.json();
    // If provided an invalid customer_id will be informed
    if("company_name" in customer[0]){
        let companyName = customer[0]["company_name"];
        document.getElementById('company_name').value = companyName;
    }
    else{
        document.getElementById('company_name').value = "INVALID CUSTOMER"
    }
});



async function getItem(itemId){
   let itemElement = document.getElementById(itemId).firstElementChild;
   console.log(itemElement.value);
   let response = await fetch('/items/' + itemElement.value);
   let item = await response.json();
   // Check if a valid item_id is provided
   if("description" in item[0]){
    let itemDescription = item[0]["description"];
    let descriptionField = document.getElementById(itemId).nextElementSibling;
    let inputDescriptionField = descriptionField.firstElementChild;
    inputDescriptionField.value = itemDescription;
   }
   else{
    let descriptionField = document.getElementById(itemId).nextElementSibling;
    let inputDescriptionField = descriptionField.firstElementChild;
    inputDescriptionField.value = "INVALID ITEM";
   }
};


function calculateTotal(lineId){
    // Get the row element
    rowElement = document.getElementById(lineId);
    // Traverse to the quantity element and get the typed value
    let lineElement = rowElement.firstElementChild;
    let itemElement = lineElement.nextElementSibling;
    let descriptionElement = itemElement.nextElementSibling;
    let quantityElement = descriptionElement.nextElementSibling;
    let quantityInput = quantityElement.firstElementChild;
    let quantity = quantityInput.value;
    // Traverse to the net_price element and get the current value
    let listPriceElement = quantityElement.nextElementSibling;
    let discountElement = listPriceElement.nextElementSibling;
    let netPriceElement = discountElement.nextElementSibling;
    let netPriceInput = netPriceElement.firstElementChild;
    let netPrice = netPriceInput.value;

    // Check net_price is a number (int or float) > 0.
    if (isNaN(netPrice) || netPrice <= 0){
        return;
    };
    // Calculate the total rounding to only 2 decimals
    let total = Math.round(((quantity * netPrice) + Number.EPSILON) * 100) / 100;
    // Get the total input element to update value
    let totalElement = netPriceElement.nextElementSibling;
    let inputOfTotal = totalElement.firstElementChild;
    inputOfTotal.setAttribute('value', total);

    // This last section will update grand totals
    let totals = document.getElementsByClassName('total');
    // Get the total net value
    let totalNetValue = 0;
    for(let i = 0; i < totals.length; i++){
        totalNetValue += parseFloat(totals[i].value);
    }
    // Get the total tax amount
    let taxAmount = Math.round(((totalNetValue * 0.18) + Number.EPSILON) * 100) / 100; // hard coded
    // Get the total tax included
    let totalTaxIncluded = totalNetValue + taxAmount;
    // Update all the values in the respective elements
    let totalNetValueElement = document.getElementById('total_net_value');
    totalNetValueElement.setAttribute('value', totalNetValue);
    let TaxAmountElement = document.getElementById('tax_amount');
    TaxAmountElement.setAttribute('value', taxAmount);
    let totalTaxIncludedElement = document.getElementById('total_tax_included');
    totalTaxIncludedElement.setAttribute('value', totalTaxIncluded);
};


function calculateNetPriceAndTotal(lineId){
    // Get the row element
    let rowElement = document.getElementById(lineId);
    // Traverse to quantity_element and get the current value
    let lineElement = rowElement.firstElementChild;
    let itemElement = lineElement.nextElementSibling;
    let descriptionElement = itemElement.nextElementSibling;
    let quantityElement = descriptionElement.nextElementSibling;
    let quantityInput = quantityElement.firstElementChild;
    let quantity = quantityInput.value;
    // Traverse to list_price and get the current value
    let listPriceElement = quantityElement.nextElementSibling;
    let inputOfListPrice = listPriceElement.firstElementChild;
    let listPrice = inputOfListPrice.value
    // Traverse to discount and get the current value
    let discountElement = listPriceElement.nextElementSibling;
    let inputOfDiscount = discountElement.firstElementChild;
    let discount = inputOfDiscount.value;
    if(!discount || discount < 0 || discount > 100){
        discount = 0;
        inputOfDiscount.value = 0
    };
    if(discount > 1){
        discount = discount / 100;
        inputOfDiscount.value = discount;
    };
    // Calculate new net_price
    let netPrice = Math.round(((listPrice * (1 - discount)) + Number.EPSILON) * 100) / 100;
    // Get the net_price element and update the value
    let netPriceElement = discountElement.nextElementSibling;
    let inputOfNetPrice = netPriceElement.firstElementChild;
    inputOfNetPrice.setAttribute('value', netPrice);
    // Get the total element and update the value
    let totalElement = netPriceElement.nextElementSibling;
    let inputOfTotal = totalElement.firstElementChild;
    let total = Math.round(((quantity * netPrice) + Number.EPSILON) * 100) / 100;
    inputOfTotal.setAttribute('value', total);


    // This last section will update grand totals
    let totals = document.getElementsByClassName('total');
    // Get the total net value
    let totalNetValue = 0;
    for(let i = 0; i < totals.length; i++){
        totalNetValue += parseFloat(totals[i].value);
    }
    // Get the total tax amount
    let taxAmount = Math.round(((totalNetValue * 0.18) + Number.EPSILON) * 100) / 100; // hard coded
    // Get the total tax included
    let totalTaxIncluded = Math.round(((totalNetValue + taxAmount) + Number.EPSILON) * 100) / 100;
    // Update all the values in the respective elements
    let totalNetValueElement = document.getElementById('total_net_value');
    totalNetValueElement.setAttribute('value', totalNetValue);
    let TaxAmountElement = document.getElementById('tax_amount');
    TaxAmountElement.setAttribute('value', taxAmount);
    let totalTaxIncludedElement = document.getElementById('total_tax_included');
    totalTaxIncludedElement.setAttribute('value', totalTaxIncluded);
};


function gatherData(){
    lines = document.getElementsByClassName("line");
    items = document.getElementsByClassName("item");
    descriptions = document.getElementsByClassName("description");
    quantities = document.getElementsByClassName("quantity");
    listPrices = document.getElementsByClassName("list_price");
    discounts = document.getElementsByClassName("discount");
    netPrices = document.getElementsByClassName("net_price");
    totals = document.getElementsByClassName("total");
    leadTimes = document.getElementsByClassName("lead_time");
    statusList = document.getElementsByClassName("status");
    rowFullList = [];
    for (let i = 0; i < lines.length; i++){
    rowLine = {};
    rowLine["line"] = lines[i].value;
    rowLine["item"] = items[i].value;
    rowLine["description"] = descriptions[i].value;
    rowLine["quantity"] = quantities[i].value;
    rowLine["list_price"] = listPrices[i].value;
    rowLine["discount"] = discounts[i].value;
    rowLine["net_price"] = netPrices[i].value;
    rowLine["total"] = totals[i].value;
    rowLine["lead_time"] = leadTimes[i].value;
    rowLine["status"] = statusList[i].value;
    rowFullList[i] = rowLine;
    };
    // Get text area element
    dataElement = document.getElementById('data');
    data = "[";
    for (let i = 0; i < rowFullList.length; i++){
        myJson = JSON.stringify(rowFullList[i]);
        data = data + myJson + ",";
    };
    data = data.substring(0, data.length - 1);
    data = data + "]";
    dataElement.innerHTML = data;
};



function gatherDataSorder(){
    lines = document.getElementsByClassName("line");
    items = document.getElementsByClassName("item");
    descriptions = document.getElementsByClassName("description");
    quantities = document.getElementsByClassName("quantity");
    listPrices = document.getElementsByClassName("list_price");
    discounts = document.getElementsByClassName("discount");
    netPrices = document.getElementsByClassName("net_price");
    totals = document.getElementsByClassName("total");
    leadTimes = document.getElementsByClassName("lead_time");
    deliveryDates = document.getElementsByClassName("delivery_date");
    statuses = document.getElementsByClassName("status");
    poNum = document.getElementsByClassName("po_num");
    quoteNum = document.getElementsByClassName("quote_num");
    rowFullList = [];
    for (let i = 0; i < lines.length; i++){
    rowLine = {};
    rowLine["line_ref"] = lines[i].value;
    rowLine["item_id"] = items[i].value;
    rowLine["description"] = descriptions[i].value;
    rowLine["quantity"] = quantities[i].value;
    rowLine["list_price"] = listPrices[i].value;
    rowLine["discount"] = discounts[i].value;
    rowLine["net_price"] = netPrices[i].value;
    rowLine["total"] = totals[i].value;
    rowLine["lead_time"] = leadTimes[i].value;
    rowLine["delivery_date"] = deliveryDates[i].value;
    rowLine["status"] = statuses[i].value;
    rowLine["po_num"] = poNum[i].value;
    if (!rowLine["po_num"]){
        rowLine["po_num"] = "0"
    };
    rowLine["quote_num"] = quoteNum[i].value;
    rowFullList[i] = rowLine;
    };
    console.log(rowFullList);
    // Get text area element
    dataElement = document.getElementById('data');
    data = "[";
    for (let i = 0; i < rowFullList.length; i++){
        myJson = JSON.stringify(rowFullList[i]);
        data = data + myJson + ",";
    };
    data = data.substring(0, data.length - 1);
    data = data + "]";
    dataElement.innerHTML = data;
};

async function getQuoteLines(){
    let quoteNum = document.getElementById('quote_no_input');
    quoteNum = quoteNum.options[quoteNum.selectedIndex].text;
    orderNum = document.getElementById('order_num')
    let response = await fetch('/get_quote_lines',
    {
        method: 'POST',
        headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
        },
        body: JSON.stringify({'quote_num': quoteNum , 'order_num': orderNum.value}),
        keepalive: true
    }
    );
    let quoteLines = await response.json();
    // Get the last sorder_line
    let lastSorderLine = document.getElementById('sorder_lines').lastElementChild;
    // Get the id of the last quote to use it fo on the new lines
    let lastSorderLineId = lastSorderLine.getAttribute('id');
    // Get the id_index by accessing the last 2 characters of the id
    let lastIdIndex = lastSorderLineId.substring(5, 7);
    // Get the template row and store it in a variable
    let templateRow = document.getElementById('template_row');
   
    for (let i = 0; i < quoteLines.length; i++){
        // Clone the row and store it in a variable
        let newSorderLine = templateRow.cloneNode(true);
        // Get the last id, update the count and change the row id
        lastIdIndex = parseInt(lastIdIndex, 10) + 1;
        let newIdIndex = lastIdIndex.toString().padStart(2, "0");
        // Form the new ids strings with element name + the new index
        let newSorderLineId = "line_" + newIdIndex;
        let newLineItemId = "item_" + newIdIndex;
        console.log(newLineItemId);
        // Change the row_if for the new sorder line
        newSorderLine.setAttribute('id', newSorderLineId);
        // Complete every line with the info in response 
        let lineTd = newSorderLine.firstElementChild;
        let lineInput = lineTd.firstElementChild;
        lineInput.value = quoteLines[i]["line_ref"];
        let itemTd = lineTd.nextElementSibling;
        itemTd.setAttribute('id', newLineItemId);
        let itemInput = itemTd.firstElementChild;
        // Change the value of the "oinput" attribute to pass the current item_id to the function 
        onInputValue = "getItem('" + newLineItemId + "')";
        itemInput.setAttribute('oninput', onInputValue);
        itemInput.value = quoteLines[i]["item_id"];
        let descriptionTd = itemTd.nextElementSibling;
        let descriptionInput = descriptionTd.firstElementChild;
        descriptionInput.value = quoteLines[i]["item_desc"];
        let quantityTd = descriptionTd.nextElementSibling;
        let quantityInput = quantityTd.firstElementChild;
        onChangeValue = "calculateTotal('" + newLineItemId + "')";
        quantityInput.setAttribute('onchange', onChangeValue);
        quantityInput.value = quoteLines[i]["quantity"];
        let listPriceTd = quantityTd.nextElementSibling;
        let listPriceInput = listPriceTd.firstElementChild;
        onChangeValue = "calculateNetPriceAndTotal('" + newLineItemId + "')";
        listPriceInput.setAttribute('onchange', onChangeValue);
        listPriceInput.value = quoteLines[i]["list_price"];
        let discountTd = listPriceTd.nextElementSibling;
        let discountInput = discountTd.firstElementChild;
        discountInput.setAttribute('onchange', onChangeValue);
        discountInput.value = quoteLines[i]["discount"];
        let netPriceTd = discountTd.nextElementSibling;
        let netPriceInput = netPriceTd.firstElementChild;
        netPriceInput.value = quoteLines[i]["net_price"];
        let totalTd = netPriceTd.nextElementSibling;
        let totalInput = totalTd.firstElementChild;
        totalInput.value = quoteLines[i]["line_net_total"];
        let leadTimeTd = totalTd.nextElementSibling;
        let leadTimeInput = leadTimeTd.firstElementChild;
        leadTimeInput.value = quoteLines[i]["lead_time"];
        let deliveryDateTd = leadTimeTd.nextElementSibling;
        let poNumTd = deliveryDateTd.nextElementSibling;
        let statusTd = poNumTd.nextElementSibling;
        let quoteNumTd = statusTd.nextElementSibling;
        let quoteNumInput = quoteNumTd.firstElementChild;
        quoteNumInput.value = quoteLines[i]["quote_num"];
        let removeTd = quoteNumTd.nextElementSibling;
        let onclickValue = "removeSorderLine('" + newSorderLineId + "')";
        removeTd.setAttribute('onclick', onclickValue);
        newSorderLine.removeAttribute('hidden')
        // Append the new line to the DOM
        console.log(newSorderLine);
        document.getElementById('sorder_lines').appendChild(newSorderLine);
    }

    // This section will update grand totals
    let totals = document.getElementsByClassName('total');
    // Get the total net value
    let totalNetValue = 0;
    for(let i = 0; i < totals.length; i++){
        totalNetValue += parseFloat(totals[i].value);
    }
    // Get the total tax amount
    let taxAmount = Math.round(((totalNetValue * 0.18) + Number.EPSILON) * 100) / 100; // hard coded
    // Get the total tax included
    let totalTaxIncluded = totalNetValue + taxAmount;
    // Update all the values in the respective elements
    let totalNetValueElement = document.getElementById('total_net_value');
    totalNetValueElement.setAttribute('value', totalNetValue);
    let TaxAmountElement = document.getElementById('tax_amount');
    TaxAmountElement.setAttribute('value', taxAmount);
    let totalTaxIncludedElement = document.getElementById('total_tax_included');
    totalTaxIncludedElement.setAttribute('value', totalTaxIncluded);
    // Hide again quote_input, add_lines and add_cancel
    let quoteInput = document.getElementById('quote_no_input');
    let addLines = document.getElementById('add_lines');
    let addCancel = document.getElementById('add_cancel');
    quoteInput.setAttribute('hidden', '');
    addLines.setAttribute('hidden', '');
    addCancel.setAttribute('hidden', '');
};

function removeSorderLine(lineId){
    // Check the line to remove is not the last one standing
    if(document.getElementById(lineId)!=document.getElementById('sorder_lines').firstElementChild || 
    document.getElementById(lineId)!=document.getElementById('sorder_lines').lastElementChild) {
        let lineToRemove = document.getElementById(lineId);
        lineToRemove.remove();

        // This section will update grand totals
        let totals = document.getElementsByClassName('total');
        // Get the total net value
        let totalNetValue = 0;
        for(let i = 0; i < totals.length; i++){
            totalNetValue += parseFloat(totals[i].value);
        }
        // Get the total tax amount
        let taxAmount = Math.round(((totalNetValue * 0.18) + Number.EPSILON) * 100) / 100; // hard coded
        // Get the total tax included
        let totalTaxIncluded = totalNetValue + taxAmount;
        // Update all the values in the respective elements
        let totalNetValueElement = document.getElementById('total_net_value');
        totalNetValueElement.setAttribute('value', totalNetValue);
        let TaxAmountElement = document.getElementById('tax_amount');
        TaxAmountElement.setAttribute('value', taxAmount);
        let totalTaxIncludedElement = document.getElementById('total_tax_included');
        totalTaxIncludedElement.setAttribute('value', totalTaxIncluded);
    }
    else{
        alert("You can't remove all the lines");
    }
};



