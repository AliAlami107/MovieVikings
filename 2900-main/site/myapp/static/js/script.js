document.addEventListener('DOMContentLoaded', function() {
    const regionSelect = document.getElementById('region-select');
    const searchRegionInput = document.getElementById('search-region');
    const searchForm = document.getElementById('search-form');

    // --- Remember Region Logic (Keep As Is) ---
    // ... (Your existing region logic) ...
    let validRegions = ['US', 'GB', 'NO', 'DE', 'FR', 'SE', 'DK']; // Fallback
    if (regionSelect) {
        validRegions = Array.from(regionSelect.options).map(opt => opt.value);
    } else {
        console.warn("Region select dropdown not found for validation list generation.");
    }

    const urlParams = new URLSearchParams(window.location.search);
    const urlRegion = urlParams.get('region');
    const savedRegion = localStorage.getItem('preferred_region');
    const defaultRegion = 'US';
    let effectiveRegion = defaultRegion;

    if (urlRegion && validRegions.includes(urlRegion.toUpperCase())) {
        effectiveRegion = urlRegion.toUpperCase();
    } else if (savedRegion && validRegions.includes(savedRegion.toUpperCase())) {
        effectiveRegion = savedRegion.toUpperCase();
    }

    const currentPath = window.location.pathname;
    const isOnPopularPage = (currentPath === '/popular/' || currentPath === '/popular');

    // REDIRECT LOGIC REMAINS THE SAME
    if (isOnPopularPage && (!urlRegion || urlRegion.toUpperCase() !== effectiveRegion)) {
        const redirectUrl = new URL(window.location.href);
        const newSearchParams = new URLSearchParams();
        newSearchParams.set('region', effectiveRegion);
        redirectUrl.search = newSearchParams.toString();
        console.log(`Redirecting to apply/correct region: ${redirectUrl.toString()}`);
        window.location.replace(redirectUrl.toString());
        return;
    }

    // SET INITIAL DROPDOWN VALUE
    if (regionSelect) {
        regionSelect.value = effectiveRegion;
    }
    // --- END: Remember Region Logic ---


    // --- Event Listeners ---

    // Region Select Logic (Keep As Is - handles preserving filters)
    if (regionSelect) {
        regionSelect.addEventListener('change', function() {
            const newRegion = this.value;
            localStorage.setItem('preferred_region', newRegion);
            const currentUrl = new URL(window.location.href);
            const params = new URLSearchParams(currentUrl.search);
            params.set('region', newRegion);
            params.delete('page');
            currentUrl.search = params.toString();
            window.location.href = currentUrl.toString();
        });
    }

    // Search Form Handling (Keep As Is)
    if (searchForm) {
       // ... (your existing search form logic) ...
       if (searchRegionInput) {
            searchRegionInput.value = effectiveRegion;
       }
       searchForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const queryInput = this.querySelector('input[name="query"]');
            const query = queryInput ? queryInput.value : '';
            const regionToSearch = regionSelect ? regionSelect.value : effectiveRegion;
            const searchUrl = new URL('/search/', window.location.origin);
            searchUrl.searchParams.set('query', query);
            searchUrl.searchParams.set('region', regionToSearch);
            window.location.href = searchUrl.toString();
       });
    }

    // --- NEW: Provider Logo Filter Interaction ---
    const providerCheckboxes = document.querySelectorAll('.provider-logo-grid .hidden-checkbox');

    providerCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            // Find the parent label wrapping this checkbox
            const label = this.closest('.provider-logo-label');
            if (label) {
                // Toggle the 'is-selected' class on the label based on the checkbox's checked state
                label.classList.toggle('is-selected', this.checked);
            }
        });
    });
    // --- END: Provider Logo Filter Interaction ---

});