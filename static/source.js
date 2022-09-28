
// Set the current date as the max allowed date in quotes.
let today = new Date()
var dd = String(today.getDate()).padStart(2, '0');
var mm = String(today.getMonth() + 1).padStart(2, '0');
var yyyy = today.getFullYear();

today = yyyy + '-' + mm + '-' + dd;
console.log(today);

quoteDate = document.querySelector('#quote_date');
quoteDate.setAttribute('max', today);
quoteDate.setAttribute('value', today);

function newLine(){
    // Get the last quote_line
    let lastLine = document.getElementById('quote_lines').lastElementChild;
    // Get the last quote_line id and store it in a variable
    let lastId = lastLine.getAttribute('id');
    // Get the id_index by accessing the last 2 characters of the id
    let lastIndex = lastId.substring(5, 7);
    // Increment the id_index by 1 for the new row
    let newIndex = parseInt(lastIndex, 10) + 1;
    let newIdIndex = newIndex.toString().padStart(2, "0");
    // Form the new id with the new index
    let newId = "line_" + newIdIndex
    
    // Clone the row and store it in a variable
    let newLine = lastLine.cloneNode(true);
    // Set the new id for the new row before updating the DOM
    newLine.id = newId;
    // Get the last element of the new line
    let newLineLastElement = newLine.lastElementChild;
    // Change the value of the "onclick" attribute to pass the current id to the function 
    onclickValue = "removeLine('" + newId + "')"
    newLineLastElement.setAttribute("onclick", onclickValue)
    document.querySelector('#quote_lines').appendChild(newLine);
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




