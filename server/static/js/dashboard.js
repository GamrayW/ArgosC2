$(document).ready(function() {
    function loadTargets() {
        $.ajax({
            url: '/api/v1/targets',
            type: 'GET',
            dataType: 'json',
            success: function(targets) {
                updateTargetsPanel(targets);
                updateTargetsList(targets);
            },
            error: function(error) {
                console.log("Erreur lors de la récupération des cibles : ", error);
            }
        });
    }

    function updateTargetsPanel(targets) {
        var targetsPanel = $('#targets-panel');
        targetsPanel.empty(); 

        $.each(targets, function(index, target) {
            var targetElement = $('<div>', {class: 'target', text: target.display_name});
            targetsPanel.append(targetElement);
        });
    }

    function updateTargetsList(targets) {
        var targetsListBody = $('#targets-list tbody');
        targetsListBody.empty(); 

        $.each(targets, function(index, target) {
            var row = $('<tr>').append(
                $('<td>').text(target.ip_addr),
                $('<td>').text(target.display_name),
                $('<td>').text(target.heartbeat) 
            );
            targetsListBody.append(row);
        });
    }


    function updateTargetsPanel(targets) {
        var targetsPanel = $('#targets-panel');
        targetsPanel.empty(); 

        $.each(targets, function(index, target) {
            var targetElement = $('<div>', {
                class: 'target',
                text: target.display_name,
                click: function() { loadCommandHistory(target.id); } 
            });
            targetsPanel.append(targetElement);
        });
    }


    function loadCommandHistory(targetId) {
        $.ajax({
            url: '/api/v1/targets',
            type: 'GET',
            dataType: 'json',
            success: function(targets) {
                var selectedTarget = targets.find(function(target) {
                    return target.id === targetId;
                });

                if (selectedTarget) {
                    $.ajax({
                        url: '/api/v1/command_history/' + targetId,
                        type: 'GET',
                        dataType: 'json',
                        success: function(commands) {
                            updateCommandTerminal(commands, selectedTarget.display_name, selectedTarget.ip_addr);
                        },
                        error: function(error) {
                            console.log("Erreur lors de la récupération de l'historique des commandes : ", error);
                        }
                    });
                }
            },
            error: function(error) {
                console.log("Erreur lors de la récupération des cibles : ", error);
            }
        });
    }

    function updateCommandTerminal(commands, hostname, ip) {
        var commandInput = $('#command-input');
        commandInput.empty();
    
        $.each(commands, function(index, command) {
            var commandText = `<div>${hostname}@${ip} $ ${command.command}</div>`;
            commandInput.append(commandText);
        });
    }
    

    loadTargets();
});
