function filterBy(metric) {
    const items = document.querySelectorAll('.leaderboard-item');
    const buttons = document.querySelectorAll('.filter-btn');

    // Update active button
    buttons.forEach(btn => btn.classList.remove('active'));
    event.target.classList.add('active');

    // Sort items
    const sortedItems = Array.from(items).sort((a, b) => {
        const aValue = parseInt(a.dataset[metric]);
        const bValue = parseInt(b.dataset[metric]);
        return bValue - aValue;
    });

    // Update order with animation
    const container = document.querySelector('.leaderboard');
    container.style.opacity = '0.5';

    setTimeout(() => {
        sortedItems.forEach(item => container.appendChild(item));
        container.style.opacity = '1';
    }, 200);
}
