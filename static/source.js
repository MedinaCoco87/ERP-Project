
// Set the current date as a 'max' allowed date in quotes.
let today = new Date()
var dd = String(today.getDate()).padStart(2, '0');
var mm = String(today.getMonth() + 1).padStart(2, '0');
var yyyy = today.getFullYear();

today = yyyy + '-' + mm + '-' + dd;
console.log(today);

quoteDate = document.querySelector('#quote_date');
quoteDate.setAttribute('max', today);


