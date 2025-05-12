let currentSlide = 0;
const images = document.querySelectorAll('.carousel-image');
const button = document.querySelectorAll('.carousel-btn')

function showSlide(index) {
  if (index >= images.length) currentSlide = 0;
  if (index < 0) currentSlide = images.length - 1;

  images.forEach((img, i) => img.style.display = i === currentSlide ? 'block' : 'none');
}

function changeSlide(direction) {
  currentSlide += direction;
  showSlide(currentSlide);
}

showSlide(currentSlide)

if (images.length === 1) {
  button.forEach((button) => button.style.display = 'none')
}

document.addEventListener('DOMContentLoaded', function() {
  var containers = document.getElementsByClassName('review-author-container');

  var colors = [
    '#FFC1CC', '#AEDFF7', '#B5EAD7', '#FFF5BA', '#E3DFFF', '#FFDAB9', '#E6E0FA', '#CFFFE5',
    '#F4C2C2', '#AEC6CF', '#C3B1E1', '#F0E4D7', '#F5C6CB', '#D4A5A5', '#B9F2D0', '#E2D1F9',
    '#F5E8C7', '#D5F5E3', '#E8DAEF', '#FADADD'
  ];

  var avalaibleColors = [...colors];

  for (var i = 0; i < containers.length; i++) {
    if (avalaibleColors.length === 0) {
      avalaibleColors = [...colors];
    }

    var randomIndex = Math.floor(Math.random() * avalaibleColors.length);
    var randomColor = avalaibleColors[randomIndex];

    containers[i].style.backgroundColor = randomColor;

    avalaibleColors.splice(randomIndex, 1)
  }
});