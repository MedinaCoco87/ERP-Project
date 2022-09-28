
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
    // Form the new ids with some meaningful string + the new index
    let newQuoteLineId = "line_" + newIdIndex
    let newItemElementId = "item_" + newIdIndex
    
    // Clone the row and store it in a variable
    let newQuoteLine = lastQuoteLine.cloneNode(true);
    // Set the a id for the new line before updating the DOM
    newQuoteLine.id = newQuoteLineId;
    // Get the last element child of the new line
    let newLineLastElement = newQuoteLine.lastElementChild;
    // Change the value of the "onclick" attribute to pass the current id to the function 
    onclickValue = "removeLine('" + newQuoteLineId + "')"
    newLineLastElement.setAttribute("onclick", onclickValue)
    // Get the "item" element of the new_line
    let newQuoteLineFirstChild = newQuoteLine.firstElementChild;
    let newItemElement = newQuoteLineFirstChild.nextElementSibling;
    // Set a new Id for the new ItemElement
    newItemElement.id = newItemElementId;
    // Get the input element inside the item element
    let inputOfItemElement = newItemElement.firstElementChild;
    // Change the value of the oninput attribute to include the current itemElementId
    onInputValue = "getItem('" + newItemElementId + "')";
    inputOfItemElement.setAttribute('oninput', onInputValue);

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




