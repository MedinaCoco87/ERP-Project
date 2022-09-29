
// Set the current date as the max allowed date in quotes.
let today = new Date()
let dd = String(today.getDate()).padStart(2, '0');
let mm = String(today.getMonth() + 1).padStart(2, '0');
let yyyy = today.getFullYear();

today = yyyy + '-' + mm + '-' + dd;
console.log(today);

quoteDate = document.querySelector('#quote_date');
quoteDate.setAttribute('max', today);
quoteDate.setAttribute('value', today);


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
    
    // Clone the row and store it in a variable
    let newQuoteLine = lastQuoteLine.cloneNode(true);
    // Set the id for the new line before updating the DOM
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



// Function to get item descriptions in forms
async function getItem(itemId){
   let itemElement = document.getElementById(itemId).firstElementChild;
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
    console.log(lineId);
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

    // Check net_price is a number (int or float) different than 0.
        // Calculate the new total
    // Else do nothing
    if (isNaN(netPrice) || netPrice <= 0){
        return;
    };
    // Calculate the total rounding to only 2 decimals
    let total = Math.round(((quantity * netPrice) + Number.EPSILON) * 100) / 100;
    // Get the total input element to update value
    let totalElement = netPriceElement.nextElementSibling;
    let inputOfTotal = totalElement.firstElementChild;
    inputOfTotal.setAttribute('value', total);
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
};

