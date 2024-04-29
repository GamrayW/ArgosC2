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
                console.log("Error retrieving order history: ", error);
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
        $('#hidden-agent-input').val(selectedAgent);  // Mise à jour de l'input caché avec l'agent sélectionné
        loadBuildConfig(selectedAgent);
    });

    function loadBuildConfig(agent) {
        $.ajax({
            url: '/api/v1/build_config',
            type: 'GET',
            data: { agent: agent },
            success: function(config) {
                populateBuildConfigForm(config, agent);
            },
            error: function(error) {
                console.log("Error retrieving build configuration:", error);
            }
        });
    }

    function populateBuildConfigForm(config, agent) {
        var form = $('#build-config-form');
        form.empty();

        form.append(`<input type="hidden" name="agent" value="${agent}">`);
    
        $.each(config, function(key, settings) {
            var formGroup = $('<div class="form-group"></div>');
            formGroup.append(`<label for="${key}">${key}</label>`); 
    
            if (settings.type === 'list') {
                var listContainer = $('<div class="list-container"></div>');
                
                var defaultValues = ""
                                
                $.each(settings.value, function(index, value) {
                    listContainer.append(`
                        <div class="value-entry">
                            <input type="text" name="${key}[]" value="${value}" class="value-input">
                            <button type="button" class="add-value">+</button>
                            <button type="button" class="remove-value">-</button>
                        </div>
                    `);

                    if (defaultValues == "") {
                        defaultValues += value 
                    } else {
                        defaultValues += "," + value
                    }
                    
                    console.log(defaultValues)
                });
                formGroup.append(listContainer);
                listContainer.append(`<input type="hidden" id="${key}" name="${key}" value="${defaultValues}">`)
            }
             else if (settings.type === 'choice') {
                var select = $(`<select name="${key}"></select>`); 
                $.each(settings.value, function(index, option) {
                    select.append(`<option value="${option}">${option}</option>`);
                });
                formGroup.append(select);
            } else if (settings.type === 'single') {
                formGroup.append(`<input type="text" name="${key}" value="${settings.value}" class="single-input">`);
            }
    
            form.append(formGroup);
        });
    
        form.append('<button type="submit" class="build-button">Build</button>');
    }
    
    
    
    function sendBuildRequest() {
        var agent = $('#agents-dropdown').val();
        $('#hidden-agent-input').val(agent);
    
        document.getElementById('build-form').submit();
    }
    

    
    $(document).on('click', '.add-value', function() {
        var newEntry = $(this).parent().clone();
        newEntry.find('input').val('');
        $(this).parent().after(newEntry);
    });
    
    $(document).on('click', '.remove-value', function() {
        if ($(this).parent().parent().find('.value-entry').length > 1) {
            $(this).parent().remove();
        } else {
            alert('Cannot remove the last entry.');
        }
    });
    

    loadTargets();
    setInterval(loadTargets, 1000);
    setInterval(updateCurrentTerminal, 1000);
    
});

