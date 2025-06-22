/**
 * Sidebar Management Script
 * Handles watchlist sidebar functionality including toggling, adding/removing items,
 * and maintaining the watchlist state
 */

/**
 * Toggles the sidebar visibility and rotates the toggle button
 */
function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    const button = document.querySelector('.sidebar-toggle-button');
    sidebar.classList.toggle('hidden');
    
    if (!sidebar.classList.contains('hidden')) {
        button.style.transform = 'rotate(180deg)';
    } else {
        button.style.transform = 'rotate(0deg)';
    }
}

/**
 * Closes the sidebar when clicking outside
 */
document.addEventListener('click', function(event) {
    const sidebar = document.getElementById('sidebar');
    const toggleButton = document.querySelector('.sidebar-toggle-button');
    
    if (!sidebar.contains(event.target) && 
        !toggleButton.contains(event.target) && 
        !sidebar.classList.contains('hidden')) {
        sidebar.classList.add('hidden');
        toggleButton.style.transform = 'rotate(0deg)';
    }
});

/**
 * Initialize watchlist functionality when DOM is loaded
 */
document.addEventListener('DOMContentLoaded', function() {
    // Handle watchlist add/remove forms
    document.querySelectorAll('.watchlist-form').forEach(form => {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            
            fetch(this.action, {
                method: 'POST',
                body: new FormData(this),
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => response.json())
            .then(data => {
                const button = this.querySelector('.watchlist-button');
                
                if (data.status === 'added') {
                    button.innerHTML = '★ In Watchlist';
                    button.classList.add('in-watchlist');
                    // Update sidebar with new item
                    updateSidebar('add', {
                        title: data.title,
                        media_type: data.media_type,
                        media_id: data.media_id
                    });
                } else if (data.status === 'removed') {
                    button.innerHTML = '☆ Add to Watchlist';
                    button.classList.remove('in-watchlist');
                    // Remove item from sidebar
                    updateSidebar('remove', data);
                }
            })
            .catch(error => console.error('Error:', error));
        });
    });
    
    // Handle remove buttons in sidebar
    document.querySelectorAll('.remove-form').forEach(form => {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            
            fetch(this.action, {
                method: 'POST',
                body: new FormData(this),
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'removed') {
                    const listItem = this.closest('.watchlist-item');
                    listItem.style.opacity = '0';
                    setTimeout(() => {
                        listItem.remove();
                        checkEmptyWatchlist();
                    }, 300);
                }
            })
            .catch(error => console.error('Error:', error));
        });
    });
});

/**
 * Updates the sidebar content based on watchlist actions
 * @param {string} action - The action to perform ('add' or 'remove')
 * @param {Object} data - The data for the action
 */
function updateSidebar(action, data) {
    const sidebarContainer = document.getElementById('sidebar');
    let watchlistContainer = sidebarContainer.querySelector('.watchlist-items');
    
    if (action === 'add') {
        // Check for existing item
        const existingItem = watchlistContainer?.querySelector(`[data-media-id="${data.media_id}"]`);
        if (existingItem) {
            return; // Don't add duplicates
        }

        // Initialize watchlist container if needed
        if (!watchlistContainer) {
            const emptyMessage = sidebarContainer.querySelector('.empty-watchlist');
            if (emptyMessage) {
                emptyMessage.remove();
            }
            
            watchlistContainer = document.createElement('ul');
            watchlistContainer.className = 'watchlist-items';
            sidebarContainer.appendChild(watchlistContainer);
        }

        // Create new watchlist item
        const newItem = document.createElement('li');
        newItem.className = 'watchlist-item';
        newItem.setAttribute('data-media-id', data.media_id);
        newItem.setAttribute('data-media-type', data.media_type);
        
        // Set item content
        newItem.innerHTML = `
            <div class="watchlist-item-content">
                <div class="watchlist-item-info">
                    <span class="watchlist-title">${data.title}</span>
                    <span class="media-type">(${data.media_type})</span>
                </div>
                <form action="/watchlist/remove/${data.media_type}/${data.media_id}/"
                      method="post"
                      class="remove-form">
                    <input type="hidden" name="csrfmiddlewaretoken" value="${getCsrfToken()}">
                    <button type="submit" class="remove-button">&times;</button>
                </form>
            </div>
        `;

        // Add remove functionality to new item
        const removeForm = newItem.querySelector('.remove-form');
        removeForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            fetch(this.action, {
                method: 'POST',
                body: new FormData(this),
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'removed') {
                    newItem.style.opacity = '0';
                    setTimeout(() => {
                        newItem.remove();
                        checkEmptyWatchlist();
                    }, 300);
                }
            })
            .catch(error => console.error('Error:', error));
        });

        // Add new item to the beginning of the list
        watchlistContainer.insertBefore(newItem, watchlistContainer.firstChild);
    } else if (action === 'remove') {
        // Remove item from watchlist
        const itemToRemove = watchlistContainer?.querySelector(`[data-media-id="${data.media_id}"]`);
        if (itemToRemove) {
            itemToRemove.remove();
            checkEmptyWatchlist();
        }
    }
}

/**
 * Checks if the watchlist is empty and shows appropriate message
 */
function checkEmptyWatchlist() {
    const sidebarContainer = document.getElementById('sidebar');
    const watchlistContainer = sidebarContainer.querySelector('.watchlist-items');
    
    if (!watchlistContainer || watchlistContainer.children.length === 0) {
        if (watchlistContainer) {
            watchlistContainer.remove();
        }
        
        if (!sidebarContainer.querySelector('.empty-watchlist')) {
            const emptyMessage = document.createElement('div');
            emptyMessage.className = 'empty-watchlist';
            emptyMessage.innerHTML = '<p>Your watchlist is empty</p>';
            sidebarContainer.appendChild(emptyMessage);
        }
    }
}

/**
 * Gets the CSRF token from the page
 * @returns {string} The CSRF token value
 */
function getCsrfToken() {
    return document.querySelector('[name=csrfmiddlewaretoken]').value;
}