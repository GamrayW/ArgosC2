$(document).ready(function() {

    var currentTargetId = null;

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
            var targetElement = $('<div>', {
                class: 'target',
                'data-id': target.id,
                'data-display-name': target.display_name,
                'data-ip': target.ip_addr,
                text: target.display_name,
                click: function() {
                    currentTargetId = target.id;

                    loadCommandHistory(target.id);

                    var newPrompt = `${target.display_name}@${target.ip_addr} $ `;
                    $('#command-prompt').text(newPrompt);
                }
            });
            targetsPanel.append(targetElement);
        });
    }

    function updateTargetsList(targets) {
        var targetsListBody = $('#targets-list tbody');
        targetsListBody.empty(); 

        let currentTime = Math.floor(Date.now() / 1000);

        $.each(targets, function(index, target) {
            let elapsed = currentTime - target.heartbeat
            
            var row = $('<tr>').append(
                $('<td>').text(target.ip_addr),
                $('<td>').text(target.display_name),
                $('<td>').text(`${elapsed}s ago`) 
            );
            targetsListBody.append(row);
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

    function focusNewCommandPrompt() {
        var newCommandPrompt = $('#new-command-prompt');
        if (newCommandPrompt.length) {
            var div = newCommandPrompt.get(0);
            var textRange = document.createRange();
            textRange.selectNodeContents(div);
            textRange.collapse(false);
            var selection = window.getSelection();
            selection.removeAllRanges();
            selection.addRange(textRange);
        }
    }
    
    $('#send-command-btn').click(function() {
        var command = $('#new-command-prompt').text().trim();
        if (!command || currentTargetId === null) {
            alert('Veuillez sélectionner une cible et entrer une commande.');
            return;
        }
    
        sendCommandToTarget(command, currentTargetId);
    });
    
    function sendCommandToTarget(command, targetId) {
        $.ajax({
            url: '/api/v1/send_command/' + targetId,
            type: 'POST',
            dataType: 'json',
            data: { cmd: command },
            success: function(response) {
                if (response.success) {
                    var currentTarget = $('.target[data-id="' + targetId + '"]');
                    var hostname = currentTarget.data('display-name');
                    var ip = currentTarget.data('ip');
                    $('#command-history').append(`<div>${hostname}@${ip} $ ${command}</div>`);
    
                    $('#new-command-prompt').empty();
    
                    focusNewCommandPrompt();
                } else {
                    alert('Erreur : ' + response.msg);
                }
            },
            error: function(xhr, status, error) {
                alert('Erreur lors de l\'envoi de la commande : ' + error);
            }
        });
    }


    loadTargets();
});
