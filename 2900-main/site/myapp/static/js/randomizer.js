/**
 * Randomizer Wheel Class
 * Manages the movie/TV show randomizer wheel functionality
 * Handles content loading, filtering, and wheel spinning animation
 */
class Wheel {
    constructor() {
        // Initialize DOM elements
        this.wheel = document.getElementById('wheel');
        this.spinButton = document.getElementById('spin-button');
        this.resultContainer = document.getElementById('result');
        this.selectedContent = document.getElementById('selected-content');
        this.mediaButtons = document.querySelectorAll('.media-button');
        this.regionSelect = document.getElementById('region-select');
        this.genreTags = document.getElementById('genre-tags');
        
        // State management
        this.content = [];
        this.filteredContent = [];
        this.currentMediaType = 'all';
        this.isSpinning = false;
        this.numberOfSegments = 12;
        this.genres = [];
        this.selectedGenres = ['all']; // Default to "All Genres"
        
        this.setupEventListeners();
        this.loadContent();
    }

    /**
     * Sets up event listeners for user interactions
     * Handles media type selection, spinning, region changes, and genre filtering
     */
    setupEventListeners() {
        // Media type button handlers
        this.mediaButtons.forEach(button => {
            button.addEventListener('click', () => {
                this.mediaButtons.forEach(btn => btn.classList.remove('active'));
                button.classList.add('active');
                this.setMediaType(button.dataset.type);
            });
        });
        
        // Spin button handler
        this.spinButton.addEventListener('click', () => this.spin());
        
        // Region selection handler
        this.regionSelect.addEventListener('change', () => this.loadContent());
        
        // Genre tag click handler with event delegation
        this.genreTags.addEventListener('click', (e) => {
            const clickedTag = e.target.closest('.genre-tag');
            if (!clickedTag) return;
            
            const genreId = clickedTag.dataset.id;
            
            // Handle "All Genres" special case
            if (genreId === 'all') {
                document.querySelectorAll('.genre-tag').forEach(tag => {
                    tag.classList.remove('active');
                });
                clickedTag.classList.add('active');
                this.selectedGenres = ['all'];
            } else {
                // Handle individual genre selection
                const allGenresTag = document.querySelector('.genre-tag[data-id="all"]');
                
                if (allGenresTag.classList.contains('active')) {
                    allGenresTag.classList.remove('active');
                    this.selectedGenres = [];
                }
                
                // Toggle genre selection
                if (clickedTag.classList.contains('active')) {
                    clickedTag.classList.remove('active');
                    this.selectedGenres = this.selectedGenres.filter(id => id !== genreId);
                    
                    // Reset to "All Genres" if no genres selected
                    if (this.selectedGenres.length === 0) {
                        allGenresTag.classList.add('active');
                        this.selectedGenres = ['all'];
                    }
                } else {
                    clickedTag.classList.add('active');
                    this.selectedGenres.push(genreId);
                }
            }
            
            this.loadContent();
        });
    }

    /**
     * Loads content from the server based on selected filters
     * Updates the wheel and genre tags accordingly
     */
    async loadContent() {
        try {
            this.spinButton.disabled = true;
            this.spinButton.textContent = '...';
            
            const region = this.regionSelect.value;
            
            // Build API URL with parameters
            let url = `/randomizer/get-random-content/?region=${region}`;
            
            // Add genre filters if selected
            if (this.selectedGenres.length > 0 && !this.selectedGenres.includes('all')) {
                this.selectedGenres.forEach(genre => {
                    url += `&genre=${genre}`;
                });
            }
            
            const response = await fetch(url);
            if (!response.ok) throw new Error('Failed to load content');
            
            const data = await response.json();
            this.content = data.results;
            
            // Update genre tags if available
            if (data.genres && data.genres.length > 0) {
                this.updateGenreTags(data.genres);
            }
            
            this.filterContent();
            
            this.spinButton.disabled = false;
            this.spinButton.textContent = 'SPIN';
        } catch (error) {
            console.error('Error loading content:', error);
            this.spinButton.textContent = 'ERR';
        }
    }

    /**
     * Updates the genre tag UI based on available genres
     * Maintains selection state of previously selected genres
     */
    updateGenreTags(genres) {
        this.genres = genres;
        
        const allGenresTag = this.genreTags.querySelector('.genre-tag[data-id="all"]');
        
        // Clear existing genre tags except "All Genres"
        Array.from(this.genreTags.children).forEach(child => {
            if (child !== allGenresTag) {
                this.genreTags.removeChild(child);
            }
        });
        
        // Create new genre tags
        genres.forEach(genre => {
            const genreTag = document.createElement('div');
            genreTag.className = 'genre-tag';
            genreTag.dataset.id = genre.id;
            genreTag.textContent = genre.name;
            
            if (this.selectedGenres.includes(String(genre.id))) {
                genreTag.classList.add('active');
            }
            
            this.genreTags.appendChild(genreTag);
        });
    }

    /**
     * Sets the current media type and filters content accordingly
     */
    setMediaType(type) {
        this.currentMediaType = type;
        this.filterContent();
    }

    /**
     * Filters content based on selected media type
     */
    filterContent() {
        this.filteredContent = this.content.filter(item => {
            if (this.currentMediaType === 'all') return true;
            return item.media_type === this.currentMediaType;
        });
        this.createWheel();
    }

    /**
     * Creates the wheel UI with segments and emojis
     */
    createWheel() {
        // Color palette for wheel segments
        const colors = [
            '#ff4444', // Primary red
            '#ff6666', // Lighter red
            '#2c3e50', // Dark blue
            '#34495e', // Lighter blue
            '#2980b9', // Bright blue
        ];

        // Emoji sets for different media types
        const movieEmojis = ['🎬', '🍿', '🎭', '🎦'];
        const tvEmojis = ['📺', '🎥', '📽️', '🎞️'];
        
        const segmentAngle = 360 / this.numberOfSegments;
        const gradientStops = [];
        
        this.wheel.innerHTML = '';
        
        // Create wheel segments
        for (let i = 0; i < this.numberOfSegments; i++) {
            const startAngle = i * segmentAngle;
            const endAngle = (i + 1) * segmentAngle;
            const colorIndex = i % colors.length;
            
            gradientStops.push(`${colors[colorIndex]} ${startAngle}deg ${endAngle}deg`);
            
            const segment = document.createElement('div');
            segment.className = 'wheel-segment';
            segment.style.transform = `rotate(${startAngle}deg)`;
            
            const emoji = document.createElement('span');
            emoji.className = 'segment-emoji';
            emoji.textContent = i % 2 === 0 ? 
                movieEmojis[Math.floor(i/2) % movieEmojis.length] : 
                tvEmojis[Math.floor(i/2) % tvEmojis.length];
            
            segment.appendChild(emoji);
            this.wheel.appendChild(segment);
        }
        
        this.wheel.style.background = `conic-gradient(${gradientStops.join(', ')})`;
    }

    /**
     * Handles the wheel spinning animation and result selection
     */
    spin() {
        if (this.isSpinning || this.filteredContent.length === 0) return;
        
        this.isSpinning = true;
        this.spinButton.disabled = true;
        this.spinButton.textContent = '...';
        this.spinButton.classList.add('spinning');
        this.resultContainer.style.display = 'none';

        const randomIndex = Math.floor(Math.random() * this.filteredContent.length);
        const spins = 5 + Math.random() * 2;
        const finalRotation = (spins * 360) + (randomIndex * (360 / this.numberOfSegments));
        
        // Reset and animate wheel
        this.wheel.style.transition = 'none';
        this.wheel.style.transform = 'rotate(0deg)';
        this.wheel.offsetHeight; // Force reflow
        this.wheel.style.transition = 'transform 4s cubic-bezier(0.22, 1, 0.36, 1)';
        this.wheel.style.transform = `rotate(${finalRotation}deg)`;
        
        setTimeout(() => this.showResult(randomIndex), 4000);
    }

    /**
     * Displays the selected content result
     */
    showResult(index) {
        const selected = this.filteredContent[index];
        
        // Format streaming providers and genres
        const streamingHtml = this.formatStreamingProviders(selected.streaming_providers);
        
        let genresHtml = '';
        if (selected.genres && selected.genres.length > 0) {
            genresHtml = `
                <div class="genres">
                    <span class="genres-label">Genres:</span>
                    <span class="genres-list">${selected.genres.map(g => g.name).join(', ')}</span>
                </div>
            `;
        }
        
        this.selectedContent.innerHTML = `
            <div class="result-card">
                <img src="${selected.poster_url}" alt="${selected.title}" class="result-poster">
                <div class="result-info">
                    <h3>
                        <a href="/${selected.media_type}/${selected.id}/" class="content-link">
                            ${selected.title}
                        </a>
                    </h3>
                    <div class="meta-info">
                        <span class="media-type">${selected.media_type === 'movie' ? 'Movie' : 'TV Show'}</span>
                        <span class="rating">★ ${selected.rating.toFixed(1)}</span>
                        <span class="votes">(${selected.vote_count} votes)</span>
                    </div>
                    ${genresHtml}
                    <p class="overview">${selected.overview}</p>
                    ${streamingHtml}
                </div>
            </div>
        `;
        
        this.resultContainer.style.display = 'block';
        this.isSpinning = false;
        this.spinButton.disabled = false;
        this.spinButton.classList.remove('spinning');
        this.spinButton.textContent = 'SPIN';
    }

    formatStreamingProviders(providers) {
        if (!providers) return '';
        
        const sections = [];
        
        if (providers.flatrate?.length) {
            sections.push(`
                <div class="streaming-section">
                    <h4>Stream on:</h4>
                    <div class="provider-list">
                        ${providers.flatrate.map(p => `
                            <div class="provider">
                                <img src="https://image.tmdb.org/t/p/original${p.logo_path}" 
                                     alt="${p.provider_name}"
                                     title="${p.provider_name}">
                            </div>
                        `).join('')}
                    </div>
                </div>
            `);
        }
        
        if (providers.rent?.length) {
            sections.push(`
                <div class="streaming-section">
                    <h4>Rent on:</h4>
                    <div class="provider-list">
                        ${providers.rent.map(p => `
                            <div class="provider">
                                <img src="https://image.tmdb.org/t/p/original${p.logo_path}" 
                                     alt="${p.provider_name}"
                                     title="${p.provider_name}">
                            </div>
                        `).join('')}
                    </div>
                </div>
            `);
        }
        
        return sections.length ? `
            <div class="streaming-providers">
                ${sections.join('')}
            </div>
        ` : '<p class="no-streaming">No streaming information available</p>';
    }
}

// Initialize the wheel when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new Wheel();
}); 