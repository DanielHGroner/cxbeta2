const logo = document.getElementById('logo');
const rightSection = document.querySelector('.right');

logo.addEventListener('click', function() {
  if (rightSection.style.display === 'none') {
    rightSection.style.display = 'block';
  } else {
    rightSection.style.display = 'none';
  }
});

const helpContainer = document.getElementById('help-container');

var helpDisplaying = true;
const helpToggleButton = document.getElementById('help-toggle');
helpToggleButton.addEventListener('click', function() {
  helpDisplaying = !helpDisplaying;
  // show or hide current help
  if (helpDisplaying && helpContainer.innerHTML != '-' && helpContainer.innerHTML != '-')
    helpContainer.style.display = "block";
  else
    helpContainer.style.display = "none";
});
