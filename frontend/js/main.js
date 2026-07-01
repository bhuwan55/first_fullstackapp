let currentBooks = [];
const searchInput = document.querySelector('.search-section input');
const searchButton = document.querySelector('.search-button');
const loadingSpinner = document.querySelector('.loading-spinner');

const STATUS_LABELS = {
  want_to_read: "Want To Read",
  reading: "Reading",
  finished: "Finished Reading"
};

async function loadBooksFromBackend() {
    const response = await fetch('http://localhost:8000/api/books')
    const data = await response.json();
    console.log(data);
    
    currentBooks = data;
    renderBooks(data)

}


window.addEventListener('DOMContentLoaded', (loadBooksFromBackend))


searchButton.addEventListener('click', async () => {
    const query = searchInput.value.trim();
    if (!query){
        alert('Please enter a search term.');
        return;
    }

    if (query.length < 3){
        alert('Please enter at least 3 characters for the search term.');
        return;
    }

    searchButton.classList.add('loading');

    try {
        const response = await fetch(`https://openlibrary.org/search.json?q=${encodeURIComponent(query)}`);
        const data = await response.json();
        console.log(data);

        const books = data.docs.slice(0, 15).map(doc => ({
            isbn: doc.key.replace('/works/', ''),
            title: doc.title,
            author_name: doc.author_name || ['Unknown Author'],
            publisher_name: doc.publisher || 'Unknown',
            started_at: doc.publishYear || doc.first_publish_year,
        }));
        console.log(books);
        currentBooks = books;
        renderBooks(books, true);
    } catch (error) {
        console.error('Error fetching search results:', error);
    }
    searchButton.classList.remove('loading');
});


function renderBooks(books, show_action=false) {
    const tableBody = document.querySelector('.table-section table tbody');
    tableBody.innerHTML = '';

    books.forEach(book => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${book.isbn}</td>
            <td>${book.title}</td>
            <td>${book.author_name}</td>
            <td>${book.publisher_name}</td>
            <td>${book.started_at}</td>
            ${show_action ? 
                `<td><button class="add-button" data-isbn="${book.isbn}">Add to Wishlist</button></td>` :
                 `<td>
                    <select class="status-select" data-isbn="${book.isbn}">
                        <option value="want_to_read" ${book.reading_status === 'want_to_read' ? 'selected' : ''}>${STATUS_LABELS.want_to_read}</option>
                        <option value="reading" ${book.reading_status === 'reading' ? 'selected' : ''}>${STATUS_LABELS.reading}</option>
                        <option value="finished" ${book.reading_status === 'finished' ? 'selected' : ''}>${STATUS_LABELS.finished}</option>
                    </select>
                 </td>`}
        `;
        tableBody.appendChild(row);
    });
}

const tableBody = document.querySelector('.table-section table tbody');

tableBody.addEventListener('click', async(event) => 
    { if (!event.target.classList.contains('add-button'))
         { return; } 
    const isbn = event.target.dataset.isbn; 
    console.log(isbn); 

    book = currentBooks.filter(book => book.isbn === isbn)[0];

    try {
        const response = await fetch('http://localhost:8000/api/books', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                isbn: isbn,
                title: book.title,
                publisher_name: book.publisher_name,
                author_name: book.author_name[0]
            })
        });

        const data = await response.json();
        console.log(data);
        if (data.success) {
            alert('Book added!');
        } else {
            alert(data.error);
        }
    } catch (error) {
        console.error(error);
    }
});


function validateStatusTransition(currentStatus, newStatus) {
    const allowedTransitions = {
        want_to_read: ['reading', 'finished'],
        reading: ['finished'],
        finished: []
    };

    if (!allowedTransitions[currentStatus].includes(newStatus)) {
        alert(`Invalid status transition from ${currentStatus} to ${newStatus}`);
        throw new Error(`Invalid status transition from ${currentStatus} to ${newStatus}`);
    }
};


tableBody.addEventListener('change', async (event) => {
    if (!event.target.classList.contains('status-select')) {
        return;
    }
    const isbn = event.target.dataset.isbn;
    const newStatus = event.target.value;

    book = currentBooks.filter(book => book.isbn === isbn)[0];

    try {
        validateStatusTransition(book.reading_status, newStatus);
    } catch (error) {
        event.target.value=book.reading_status; // Revert to previous status
        return;
    }

    console.log(currentBooks);
    try {
        const response = await fetch(`http://localhost:8000/api/books/${isbn}`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                book_id: book.id,
                reading_status: newStatus
            })
        });

        const data = await response.json();
        console.log(data);
        if (data.success) {
            alert('Status updated!');
        } else {
            alert(data.error);
        }
    } catch (error) {
        console.error(error);
    }
});