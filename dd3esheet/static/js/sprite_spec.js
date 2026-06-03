/* Art Direction Spec - scroll-spy do sumario (TOC).
   Espelha design_handoff_dnd_vtt/app/spec-render.js: marca o item
   ativo conforme a secao entra na viewport, via IntersectionObserver. */
(function () {
  'use strict';

  var links = Array.prototype.slice.call(
    document.querySelectorAll('.ss-toc a[data-spy]')
  );
  if (!links.length || !('IntersectionObserver' in window)) {
    return;
  }

  var linkById = {};
  var sections = [];
  links.forEach(function (link) {
    var id = link.getAttribute('data-spy');
    var section = document.getElementById(id);
    if (section) {
      linkById[id] = link;
      sections.push(section);
    }
  });

  function setActive(id) {
    links.forEach(function (link) {
      link.classList.toggle('is-active', link.getAttribute('data-spy') === id);
    });
  }

  var visible = {};
  var observer = new IntersectionObserver(function (entries) {
    entries.forEach(function (entry) {
      if (entry.isIntersecting) {
        visible[entry.target.id] = entry.intersectionRatio;
      } else {
        delete visible[entry.target.id];
      }
    });

    var bestId = null;
    var bestRatio = -1;
    Object.keys(visible).forEach(function (id) {
      if (visible[id] > bestRatio) {
        bestRatio = visible[id];
        bestId = id;
      }
    });
    if (bestId) {
      setActive(bestId);
    }
  }, {
    // foca na banda superior da viewport para antecipar a secao corrente
    rootMargin: '-10% 0px -55% 0px',
    threshold: [0, 0.25, 0.5, 0.75, 1],
  });

  sections.forEach(function (section) { observer.observe(section); });

  // estado inicial
  setActive(sections[0].id);
})();
