document.addEventListener('DOMContentLoaded', function() {
  var containers = document.getElementsByClassName('review-game-container');

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