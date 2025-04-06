  const API_BASE_URL = 'http://127.0.0.1:8000/farm/';
        const USER_API_URL = 'http://127.0.0.1:8000/users/';

        $(document).ready(function() {
            const token = localStorage.getItem('adminToken');
            if (!token) {
                window.location.href = '/adminpage';
                return;
            }

            $.ajaxSetup({
                headers: {
                    'Authorization': 'Token ' + token
                }
            });

            loadOwners();
            addMotorInput();
            loadDashboardData();
            fetchUsers();
        });

        function toggleDrawer() {
            const drawer = document.getElementById('drawer');
            const content = document.getElementById('content');
            drawer.classList.toggle('open');
            content.classList.toggle('shifted');
        }

        function logout() {
            localStorage.removeItem('adminToken');
            window.location.href = '/adminpage';
        }

        function showSection(sectionId) {
            $('.section').removeClass('active');
            $('.nav-btn').removeClass('active');
            $(`#${sectionId}-section`).addClass('active');
            $(`#${sectionId}-btn`).addClass('active');
            if (sectionId === 'farm-list') listFarms();
            if (sectionId === 'dashboard') loadDashboardData();
            if (sectionId === 'user-list') fetchUsers();
        }

        $('.nav-btn').click(function() {
            const section = this.id.replace('-btn', '');
            showSection(section);
        });

        function showNotification(message, type = 'success') {
            const notification = $('#notification');
            notification.text(message).removeClass('success error').addClass(type).show();
            setTimeout(() => notification.hide(), 3000);
        }

        function getCsrfToken() {
            const cookieValue = document.cookie.split('; ').find(row => row.startsWith('csrftoken='))?.split('=')[1];
            return cookieValue;
        }

        // Farm Management Functions
        function loadOwners() {
            $.ajax({
                url: USER_API_URL,
                method: 'GET',
                success: function(users) {
                    const ownerSelect = $('#farm-owner');
                    if (!users || users.length === 0) {
                        $('#owner-error').text('No users found');
                        return;
                    }
                    users.forEach(user => {
                        ownerSelect.append(
                            `<option value="${user.id}">${user.email} (${user.role})</option>`
                        );
                    });
                    $('#owner-error').text('');
                },
                error: function(xhr) {
                    $('#owner-error').text(`Failed to load owners: ${xhr.status} - ${xhr.statusText}`);
                }
            });
        }

        let motorCount = 0;

        function addMotorInput(motor = null) {
            motorCount++;
            const motorHtml = `
                <div class="motor-input flex gap-4 mb-4" id="motor-${motorCount}">
                    <input type="number" id="UIN-${motorCount}" value="${motor?.UIN || ''}" placeholder="UIN" class="flex-1" onblur="checkUIN(${motorCount}, '${motor?.id || ''}')">
                    <input type="hidden" id="motor-id-${motorCount}" value="${motor?.id || ''}">
                    <select id="motor-type-${motorCount}" class="flex-1">
                        <option value="single_phase" ${motor?.motor_type === 'single_phase' ? 'selected' : ''}>Single Phase</option>
                        <option value="double_phase" ${motor?.motor_type === 'double_phase' ? 'selected' : ''}>Double Phase</option>
                        <option value="triple_phase" ${motor?.motor_type === 'triple_phase' ? 'selected' : ''}>Triple Phase</option>
                    </select>
                    <input type="number" id="valve-count-${motorCount}" placeholder="Valve Count" min="1" value="${motor?.valve_count || ''}" class="flex-1">
                    <button type="button" onclick="$('#motor-${motorCount}').remove()" class="btn-danger">Remove</button>
                </div>
            `;
            $('#motor-inputs').append(motorHtml);
        }

        function checkUIN(count, currentMotorId) {
            const uinInput = $(`#UIN-${count}`);
            const uinValue = uinInput.val();
            if (!uinValue) return;

            $.ajax({
                url: `${API_BASE_URL}motors/`,
                method: 'GET',
                success: function(motors) {
                    const existingMotor = motors.find(motor => motor.UIN == uinValue && motor.id != currentMotorId);
                    if (existingMotor) {
                        showNotification(`The UIN ${uinValue} is already taken by Motor ID: ${existingMotor.id}`, 'error');
                        uinInput.val('');
                    }
                },
                error: function(xhr) {
                    showNotification(`Error checking UIN: ${xhr.statusText}`, 'error');
                }
            });
        }

        function saveFarm() {
    const farmId = $('#farm-edit-id').val();
    const motors = [];

    let hasError = false;
    $('#motor-inputs .motor-input').each(function() {
        const motorId = $(this).find('input[id^="motor-id-"]').val();
        const motorUIN = $(this).find('input[id^="UIN-"]').val();
        const motorType = $(this).find('select[id^="motor-type-"]').val();
        const valveCount = parseInt($(this).find('input[id^="valve-count-"]').val());

        if (isNaN(valveCount) || valveCount < 1) {
            showNotification('Please enter a valid valve count', 'error');
            hasError = true;
            return false;
        }

        // Create motor object with all fields
        const motorObject = {
            motor_type: motorType,
            valve_count: valveCount
        };

        // Include ID for existing motors
        if (motorId) {
            motorObject.id = motorId;
        }

        // Include UIN field always (can be empty string or valid UIN)
        // This allows backend to receive UIN updates or nulls
        motorObject.UIN = motorUIN || null;

        motors.push(motorObject);
    });

    if (hasError) return;
    if (motors.length === 0) {
        showNotification('Please add at least one motor', 'error');
        return;
    }

    const farmData = {
        name: $('#farm-name').val() || 'Unnamed Farm',
        location: $('#farm-location').val() || 'Unknown Location',
        owner: parseInt($('#farm-owner').val()),
        motors: motors
    };

    const method = farmId ? 'PUT' : 'POST';
    const url = farmId ? `${API_BASE_URL}farms/${farmId}/` : `${API_BASE_URL}farms/`;

    $.ajax({
        url: url,
        method: method,
        contentType: 'application/json',
        data: JSON.stringify(farmData),
        success: function(response) {
            showNotification(`Farm ${farmId ? 'updated' : 'created'} with ID: ${response.id}`);
            resetFarmForm();
            showSection('farm-list');
            listFarms();
        },
        error: function(xhr) {
            const errorResponse = JSON.parse(xhr.responseText);
            let errorMessage = 'Error saving farm: ';

            // Handle specific error messages
            if (errorResponse.motors && Array.isArray(errorResponse.motors)) {
                errorResponse.motors.forEach((motorError, index) => {
                    if (motorError.UIN) {
                        errorMessage += `Motor #${index+1}: ${motorError.UIN[0]} `;
                    }
                });
            } else {
                errorMessage += xhr.responseText;
            }

            showNotification(errorMessage, 'error');
        }
    });
}

        function resetFarmForm() {
            $('#farm-edit-id').val('');
            $('#farm-name, #farm-location').val('');
            $('#farm-owner').val('');
            $('#motor-inputs').empty();
            motorCount = 0;
            addMotorInput();
        }

        function listFarms() {
            $.ajax({
                url: `${API_BASE_URL}farms/`,
                method: 'GET',
                success: function(farms) {
                    let html = '';
                    farms.forEach(farm => {
                        html += `
                            <div class="mb-4 p-4 bg-white rounded-lg shadow">
                                <h3>${farm.name} (ID: ${farm.id}) - ${farm.location}</h3>
                                <p>Owner ID: ${farm.owner}</p>
                                <p>Motors: ${farm.motors.length}</p>
                                <div class="flex gap-2 mt-2">
                                    <button onclick="editFarm(${farm.id})" class="btn-primary">Edit</button>
                                    <button onclick="deleteFarm(${farm.id})" class="btn-danger">Delete</button>
                                    <button onclick="viewFarmDetails(${farm.id})" class="btn-primary">View Details</button>
                                </div>
                            </div>
                        `;
                    });
                    $('#farm-list').html(html);
                },
                error: function(xhr) {
                    $('#farm-list').html(`<p class="text-danger">Error: ${xhr.responseText}</p>`);
                }
            });
        }

        function editFarm(farmId) {
            $.ajax({
                url: `${API_BASE_URL}farms/${farmId}/`,
                method: 'GET',
                success: function(farm) {
                    $('#farm-edit-id').val(farm.id);
                    $('#farm-name').val(farm.name);
                    $('#farm-location').val(farm.location);
                    $('#farm-owner').val(farm.owner);
                    $('#motor-inputs').empty();
                    motorCount = 0;
                    farm.motors.forEach(motor => addMotorInput(motor));
                    showSection('create-farm');
                },
                error: function(xhr) {
                    showNotification('Error loading farm: ' + xhr.responseText, 'error');
                }
            });
        }

        function deleteFarm(farmId) {
            if (confirm('Are you sure you want to delete this farm?')) {
                $.ajax({
                    url: `${API_BASE_URL}farms/${farmId}/`,
                    method: 'DELETE',
                    success: function() {
                        showNotification('Farm deleted');
                        listFarms();
                    },
                    error: function(xhr) {
                        showNotification('Error deleting farm: ' + xhr.responseText, 'error');
                    }
                });
            }
        }

        function getFarmData() {
            const farmId = $('#farm-id').val();
            if (!farmId) {
                $('#farm-data').html('<p>Please enter a Farm ID</p>');
                return;
            }
            $.ajax({
                url: `${API_BASE_URL}farms/${farmId}/`,
                method: 'GET',
                success: function(data) {
                    displayFarmData(data);
                },
                error: function(xhr) {
                    $('#farm-data').html(`<p class="text-danger">Error: ${xhr.responseText}</p>`);
                }
            });
        }

        function displayFarmData(data) {
            let html = `
                <h3>${data.name} - ${data.location}</h3>
                <p>Owner ID: ${data.owner || 'Not assigned'}</p>
                <h4 class="mt-4">Motors and Valves:</h4>
            `;
            if (data.motors && data.motors.length > 0) {
                data.motors.forEach(motor => {
                    html += `
                        <div class="p-4 bg-white rounded-lg shadow mt-2">
                            <h4>Motor ${motor.id} (${motor.motor_type}) - ${motor.valve_count} valves - Status: ${motor.is_active ? 'On' : 'Off'}</h4>
                            <div class="flex gap-2 mt-2">
                                <button onclick="editMotor(${motor.id}, ${data.id})" class="btn-primary">Edit</button>
                                <button onclick="deleteMotor(${motor.id}, ${data.id})" class="btn-danger">Delete</button>
                                <button onclick="toggleMotor(${motor.id}, ${motor.is_active})" class="${motor.is_active ? 'btn-danger' : 'btn-primary'}">${motor.is_active ? 'Turn Off' : 'Turn On'}</button>
                            </div>
                    `;
                    if (motor.valves && motor.valves.length > 0) {
                        motor.valves.forEach(valve => {
                            html += `
                                <div class="flex items-center gap-2 mt-1">
                                    ${valve.name} (ID: ${valve.id}) - Status: ${valve.is_active ? 'Active' : 'Inactive'}
                                    <button onclick="toggleValve(${valve.id}, ${valve.is_active})" class="btn-primary">Toggle</button>
                                </div>
                            `;
                        });
                    } else {
                        html += `<p>No valves assigned yet</p>`;
                    }
                    html += `</div>`;
                });
            } else {
                html += `<p>No motors assigned to this farm</p>`;
            }
            $('#farm-data').html(html);
        }

        function editMotor(motorId, farmId) {
            $.ajax({
                url: `${API_BASE_URL}motors/${motorId}/`,
                method: 'GET',
                success: function(motor) {
                    editFarm(farmId);
                    setTimeout(() => {
                        for (let i = 1; i <= motorCount; i++) {
                            if ($(`#motor-id-${i}`).val() == motorId) {
                                $(`#UIN-${i}`).val(motor.UIN);
                                $(`#motor-type-${i}`).val(motor.motor_type);
                                $(`#valve-count-${i}`).val(motor.valve_count);
                                break;
                            }
                        }
                    }, 100);
                },
                error: function(xhr) {
                    showNotification('Error loading motor: ' + xhr.responseText, 'error');
                }
            });
        }

        function deleteMotor(motorId, farmId) {
            if (confirm('Are you sure you want to delete this motor?')) {
                $.ajax({
                    url: `${API_BASE_URL}motors/${motorId}/`,
                    method: 'DELETE',
                    success: function() {
                        showNotification('Motor deleted');
                        listFarms();
                        if ($('#farm-edit-id').val() == farmId) editFarm(farmId);
                    },
                    error: function(xhr) {
                        showNotification('Error deleting motor: ' + xhr.responseText, 'error');
                    }
                });
            }
        }

        function toggleValve(valveId, currentStatus) {
            const newStatus = currentStatus === 1 ? 0 : 1;
            const valveElement = $(`#farm-data .valve:contains('(ID: ${valveId})')`);
            const valveText = valveElement.text();
            const valveNameMatch = valveText.match(/^(.*)\s\(ID:/);
            const valveName = valveNameMatch ? valveNameMatch[1].trim() : `Valve ${valveId}`;

            $.ajax({
                url: `${API_BASE_URL}valves/${valveId}/`,
                method: 'PUT',
                contentType: 'application/json',
                data: JSON.stringify({ name: valveName, is_active: newStatus }),
                success: function() {
                    getFarmData();
                    listFarms();
                },
                error: function(xhr) {
                    showNotification('Error toggling valve: ' + xhr.responseText, 'error');
                }
            });
        }

        function toggleMotor(motorId, currentStatus) {
            const newStatus = currentStatus === 1 ? 0 : 1;
            $.ajax({
                url: `${API_BASE_URL}motors/${motorId}/`,
                method: 'PATCH',
                contentType: 'application/json',
                data: JSON.stringify({ is_active: newStatus }),
                success: function() {
                    getFarmData();
                    listFarms();
                },
                error: function(xhr) {
                    showNotification('Error toggling motor: ' + xhr.responseText, 'error');
                }
            });
        }

        function viewFarmDetails(farmId) {
            $('#farm-id').val(farmId);
            getFarmData();
            showSection('farm-details');
        }

        function loadDashboardData() {
            $.ajax({
                url: `${API_BASE_URL}farms/`,
                method: 'GET',
                success: function(farms) {
                    $('#total-farms').text(farms.length);
                    const totalMotors = farms.reduce((sum, farm) => sum + farm.motors.length, 0);
                    $('#total-motors').text(totalMotors);
                    const totalValves = farms.reduce((sum, farm) => sum + farm.motors.reduce((vSum, motor) => vSum + (motor.valves ? motor.valves.length : 0), 0), 0);
                    $('#total-valves').text(totalValves);
                },
                error: function(xhr) {
                    showNotification('Error loading farm data: ' + xhr.responseText, 'error');
                }
            });

            $.ajax({
                url: USER_API_URL,
                method: 'GET',
                success: function(users) {
                    $('#total-users').text(users.length);
                },
                error: function(xhr) {
                    showNotification('Error loading user data: ' + xhr.responseText, 'error');
                }
            });
        }

        // User Management Functions
        let currentUserId = null;

        function fetchUsers() {
            $('#loadingIndicator').removeClass('hidden');
            $.ajax({
                url: USER_API_URL,
                type: 'GET',
                dataType: 'json',
                success: function(data) {
                    renderUserTable(data);
                    $('#loadingIndicator').addClass('hidden');
                },
                error: function(xhr) {
                    $('#loadingIndicator').addClass('hidden');
                    showNotification('Failed to load users: ' + xhr.statusText, 'error');
                }
            });
        }

        function renderUserTable(users) {
            const userTable = $('#userTable');
            userTable.empty();

            users.forEach(user => {
                userTable.append(`
                    <tr>
                        <td>${user.id}</td>
                        <td>${user.username}</td>
                        <td>${user.email}</td>
                        <td>${user.first_name || ''}</td>
                        <td>${user.last_name || ''}</td>
                        <td>${user.role || 'N/A'}</td>
                        <td>${user.is_active ? 'Active' : 'Inactive'}</td>
                        <td>
                            <button onclick="fetchUserDetails(${user.id})" class="btn-primary">Edit</button>
                            <button onclick="showDeleteConfirmation(${user.id})" class="btn-danger">Delete</button>
                        </td>
                    </tr>
                `);
            });
        }

        function fetchUserDetails(userId) {
            $.ajax({
                url: `${USER_API_URL}${userId}/`,
                type: 'GET',
                dataType: 'json',
                success: function(user) {
                    populateUserForm(user);
                    currentUserId = user.id;
                    $('#userFormTitle').text('Edit User');
                    $('#passwordHint').removeClass('hidden');
                    showSection('create-user');
                },
                error: function(xhr) {
                    showNotification('Failed to load user details: ' + xhr.statusText, 'error');
                }
            });
        }

        function populateUserForm(user) {
            $('#userId').val(user.id);
            $('#username').val(user.username);
            $('#email').val(user.email);
            $('#firstName').val(user.first_name || '');
            $('#lastName').val(user.last_name || '');
            $('#role').val(user.role || 'user');
            $('#isActive').prop('checked', user.is_active);
            $('#phoneNumber').val(user.phone_number || '');
            $('#address').val(user.address || '');
            $('#password').val('');
            $('#confirmPassword').val('');
        }

        function showDeleteConfirmation(userId) {
            currentUserId = userId;
            if (confirm('Are you sure you want to delete this user?')) {
                deleteUser(userId);
            }
        }

        function createUser(userData) {
            $.ajax({
                url: USER_API_URL,
                type: 'POST',
                contentType: 'application/json',
                data: JSON.stringify(userData),
                headers: { 'X-CSRFToken': getCsrfToken() },
                success: function() {
                    showNotification('User created successfully');
                    resetUserForm();
                    showSection('user-list');
                    fetchUsers();
                },
                error: function(xhr) {
                    showNotification('Failed to create user: ' + xhr.responseText, 'error');
                }
            });
        }

        function updateUser(userId, userData) {
            $.ajax({
                url: `${USER_API_URL}${userId}/`,
                type: 'PUT',
                contentType: 'application/json',
                data: JSON.stringify(userData),
                headers: { 'X-CSRFToken': getCsrfToken() },
                success: function() {
                    showNotification('User updated successfully');
                    resetUserForm();
                    showSection('user-list');
                    fetchUsers();
                },
                error: function(xhr) {
                    showNotification('Failed to update user: ' + xhr.responseText, 'error');
                }
            });
        }

        function deleteUser(userId) {
            $.ajax({
                url: `${USER_API_URL}${userId}/`,
                type: 'DELETE',
                headers: { 'X-CSRFToken': getCsrfToken() },
                success: function() {
                    showNotification('User deleted successfully');
                    fetchUsers();
                },
                error: function(xhr) {
                    showNotification('Failed to delete user: ' + xhr.statusText, 'error');
                }
            });
        }

        function gatherUserFormData() {
            const userData = {
                username: $('#username').val(),
                email: $('#email').val(),
                first_name: $('#firstName').val(),
                last_name: $('#lastName').val(),
                role: $('#role').val(),
                is_active: $('#isActive').is(':checked'),
                phone_number: $('#phoneNumber').val(),
                address: $('#address').val()
            };

            const password = $('#password').val();
            const confirmPassword = $('#confirmPassword').val();

            if (password) {
                if (password !== confirmPassword) {
                    showNotification('Passwords do not match', 'error');
                    return null;
                }
                userData.password = password;
            }

            return userData;
        }

        function resetUserForm() {
            $('#userForm')[0].reset();
            $('#userId').val('');
            currentUserId = null;
            $('#userFormTitle').text('Create New User');
            $('#passwordHint').addClass('hidden');
        }

        $('#addUserBtn').click(function() {
            resetUserForm();
            showSection('create-user');
        });

        $('#saveUserBtn').click(function() {
            const userData = gatherUserFormData();
            if (!userData) return;

            if (currentUserId) {
                updateUser(currentUserId, userData);
            } else {
                createUser(userData);
            }
        });