$(document).ready(function() {
    $(".draggable-container").droppable({
        drop: function(event, ui) {
            // ajouter la fonction pour le dépot de cible , à voir comment faire
        }
    });

    $(".target").draggable({
        containment: 'document',
        revert: 'invalid',
        helper: 'clone',
        cursor: 'move'
    });

    // Ajouter plus de logique ici pour les interactions avec le terminal et les boutons
});
