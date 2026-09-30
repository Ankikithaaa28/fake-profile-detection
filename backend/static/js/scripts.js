// Simple scroll animation (future upgrade ideas)
// Right now basic smooth experience
console.log("AuthentIQ loaded successfully.");

document.addEventListener('DOMContentLoaded', () => {
    const counters = document.querySelectorAll('.count');
    counters.forEach(counter => {
      const target = +counter.getAttribute('data-target');
      let count = 0;
      const step = target / 100;
  
      function update() {
        count += step;
        if (count < target) {
          counter.innerText = Math.floor(count);
          requestAnimationFrame(update);
        } else {
          counter.innerText = target;
        }
      }
  
      update();
    });
  });
  