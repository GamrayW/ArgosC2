$(document).ready(function() {
    var currentTargetId = null;
    var currentHostname = null;
    var currentIp = null;

    loadTargets();

    $('#shell-input').keypress(function(event) { 
        if (event.which == 13) {  
            event.preventDefault();  
            var command = $(this).text().trim();  
            if (command && currentTargetId) {  
                sendCommand(currentTargetId, command);
                $(this).empty(); 
            } else {
                alert('Please select a target and enter a command.');
            }
        }
    });


    function sendCommand(targetId, command) {
        $.ajax({
            url: '/api/v1/send_command/' + targetId,
            type: 'POST',
            data: {cmd: command},
            success: function(response) {
                if (response.success) {
                    var shellText = $('#shell-target').text().trim();
                    var hostname = shellText.split('@')[0];
                    var ip = shellText.substring(shellText.indexOf('@') + 1, shellText.indexOf(' $'));
                    loadCommandHistory(targetId, hostname, ip);
                } else {
                    alert('Failed to send command: ' + response.msg);
                }
            },
            error: function(xhr, status, error) {
                alert('Error sending command: ' + error);
            }
        });
    }
    


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
                console.log("Error fetching targets: ", error);
            }
        });
    }


    function updateTargetsPanel(targets) {
        var targetsPanel = $('#targets-panel');
        targetsPanel.empty(); 

        $.each(targets, function(index, target) {
            var targetElement = $('<div>', {
                class: 'target',
                text: target.display_name,
                'data-ip': target.ip_addr,
                click: function() {
                    currentTargetId = target.id;
                    currentHostname = target.display_name;
                    currentIp = target.ip_addr;
                    var shellPrompt = target.display_name + '@' + target.ip_addr + ' $ ';
                    $('#shell-target').text(shellPrompt);
                    loadCommandHistory(target.id, target.display_name, target.ip_addr);
                }
            });
            targetsPanel.append(targetElement);
        });
    }

    function updateTargetsList(targets) {
        var targetsListBody = $('#targets-list tbody');
        targetsListBody.empty(); 

        var currentTime = Math.floor(new Date().getTime()/1000);

        $.each(targets, function(index, target) {
            var row = $('<tr>').append(
                $('<td>').text(target.ip_addr),
                $('<td>').text(target.display_name),
                $('<td>').text(`${currentTime - target.heartbeat}s ago`)
            );
            targetsListBody.append(row);
        });
    }

    function loadCommandHistory(targetId, hostname, ip) {
        if (!targetId) return;
        $.ajax({
            url: '/api/v1/command_history/' + targetId,
            type: 'GET',
            dataType: 'json',
            success: function(commands) {
                updateCommandTerminal(commands, hostname, ip); 
            },
            error: function(error) {
                console.log("Erreur lors de la récupération de l'historique des commandes : ", error);
            }
        });
    }

    function updateCommandTerminal(commands, hostname, ip) {
        var commandHistory = $('#command-history');
        commandHistory.empty();
    
        $.each(commands, function(index, command) {
            var commandText = `<div>${hostname}@${ip} $ ${command.command}</div>`;
            commandHistory.append(commandText);
            if (command.response && command.response.trim() !== "") {
                var responseText = `<div class="command-response">${command.response.replace(/\n/g, '<br>')}</div>`; 
                commandHistory.append(responseText);
            }
        });
    }
    
    function updateCurrentTerminal() {
        if (currentTargetId) {
            loadCommandHistory(currentTargetId, currentHostname, currentIp);
        }
    }

    $('#payload-btn').click(function() {
        $.ajax({
            url: '/api/v1/agents_list',
            type: 'GET',
            dataType: 'json',
            success: function(agents) {
                populateAgentsDropdown(agents);
                $('#payload-modal').show();
                if (agents.length > 0) {
                    loadBuildConfig(agents[0]);
                }
            },
            error: function(error) {
                console.log("Error fetching agents list: ", error);
                alert('Failed to load agents list.');
            }
        });
    });
    $(document).on('click', '.close-button', function() {
        $('#payload-modal').hide();
    });

    $(window).click(function(event) {
        if ($(event.target).is('#payload-modal')) {
            $('#payload-modal').hide();
        }
    });

    function populateAgentsDropdown(agents) {
        var dropdown = $('#agents-dropdown');
        dropdown.empty();
        $.each(agents, function(index, agent) {
            dropdown.append($('<option></option>').attr('value', agent).text(agent));
        });
    }

    $('#agents-dropdown').change(function() {
        var selectedAgent = $(this).val();
        loadBuildConfig(selectedAgent);
    });

    function loadBuildConfig(agent) {
        $.ajax({
            url: '/api/v1/build_config',
            type: 'GET',
            data: { agent: agent },
            success: function(config) {
                populateBuildConfigForm(config);
            },
            error: function(error) {
                console.log("Erreur lors de la récupération de la configuration de build : ", error);
            }
        });
    }

    function populateBuildConfigForm(config) {
        var form = $('#build-config-form');
        form.empty();
    
        $.each(config, function(key, settings) {
            var formGroup = $('<div class="form-group"></div>');
            formGroup.append(`<label>${key}</label>`);
    
            if (settings.type === 'list') {
                var listContainer = $('<div class="list-container"></div>');
                $.each(settings.value, function(index, ip) {
                    listContainer.append(`
                        <div class="ip-entry">
                            <input type="text" value="${ip}">
                            <button type="button" class="add-ip">+</button>
                            <button type="button" class="remove-ip">-</button>
                        </div>
                    `);
                });
                formGroup.append(listContainer);
            } else if (settings.type === 'choice') {
                var select = $('<select></select>');
                $.each(settings.value, function(index, port) {
                    select.append(`<option value="${port}">${port}</option>`);
                });
                formGroup.append(select);
            } else if (settings.type === 'single') {
                formGroup.append(`<input type="text" value="${settings.value}">`);
            }
    
            form.append(formGroup);
        });
    
        form.append('<button type="submit">Save</button>');
    }
    
    $(document).on('click', '.add-ip', function() {
        var newEntry = $(this).parent().clone();
        newEntry.find('input').val('');
        $(this).parent().after(newEntry);
    });
    
    $(document).on('click', '.remove-ip', function() {
        if ($(this).parent().parent().find('.ip-entry').length > 1) {
            $(this).parent().remove();
        } else {
            alert('Cannot remove the last entry.');
        }
    });
    

    loadTargets();
    setInterval(loadTargets, 1000);
    setInterval(updateCurrentTerminal, 1000);
    
});

