document.addEventListener('DOMContentLoaded', () => {
    const containers = document.querySelectorAll('.game-feed-container');
    ms = 200
    containers.forEach((container, index) => {
        ms -= 2
        setTimeout(() => {
            container.classList.remove('loading');
        }, index * ms);
    });
});