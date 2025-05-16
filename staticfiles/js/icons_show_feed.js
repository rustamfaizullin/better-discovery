document.addEventListener('DOMContentLoaded', () => {
    const containers = document.querySelectorAll('.game-feed-container');
    ms = 30
    containers.forEach((container, index) => {
        if (ms > 1) ms -= 1
        setTimeout(() => {
            container.classList.remove('loading');
        }, index * ms);
    });
});