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
                        showNotification('No users found', 'error');
                        return;
                    }
                    users.forEach(user => {
                        ownerSelect.append(
                            `<option value="${user.id}">${user.email} (${user.role})</option>`
                        );
                    });
                },
                error: function(xhr) {
                    showNotification(`Failed to load owners: ${xhr.statusText}`, 'error');
                }
            });
        }

        let motorCount = 0;

        function addMotorInput(motor = null) {
            motorCount++;
            const motorHtml = `
                <div class="motor-input form-grid" id="motor-${motorCount}">
                    <div>
                        <label>UIN</label>
                        <input type="number" id="UIN-${motorCount}" value="${motor?.UIN || ''}" placeholder="UIN" onblur="checkUIN(${motorCount}, '${motor?.id || ''}')">
                    </div>
                    <div>
                        <label>Motor Type</label>
                        <select id="motor-type-${motorCount}">
                            <option value="single_phase" ${motor?.motor_type === 'single_phase' ? 'selected' : ''}>Single Phase</option>
                            <option value="double_phase" ${motor?.motor_type === 'double_phase' ? 'selected' : ''}>Double Phase</option>
                            <option value="triple_phase" ${motor?.motor_type === 'triple_phase' ? 'selected' : ''}>Triple Phase</option>
                        </select>
                    </div>
                    <div>
                        <label>Valve Count</label>
                        <input type="number" id="valve-count-${motorCount}" placeholder="Valve Count" min="1" value="${motor?.valve_count || ''}">
                    </div>
                    <input type="hidden" id="motor-id-${motorCount}" value="${motor?.id || ''}">
                    <div class="form-actions">
                        <button type="button" onclick="$('#motor-${motorCount}').remove()" class="btn btn-danger">
                            <i class="fas fa-trash"></i> Remove
                        </button>
                    </div>
                </div>
            `;
            $('#motor-inputs').append(motorHtml);
        }


        function saveFarm() {
            const farmId = $('#farm-edit-id').val();
            const motors = [];

            let hasError = false;
            $('#motor-inputs .motor-input').each(function() {
                const motorUIN = $(this).find('input[id^="UIN-"]').val();
                const motorType = $(this).find('select[id^="motor-type-"]').val();
                const valveCount = parseInt($(this).find('input[id^="valve-count-"]').val());
                const motorId = $(this).find('input[id^="motor-id-"]').val();

                if (isNaN(valveCount) || valveCount < 1) {
                    showNotification('Please enter a valid valve count', 'error');
                    hasError = true;
                    return false;
                }

                motors.push({
                    UIN: motorUIN,
                    id: motorId || undefined,
                    motor_type: motorType,
                    valve_count: valveCount
                });
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
                    showNotification('Error saving farm: ' + xhr.responseText, 'error');
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
                    let html = '<table class="table"><thead><tr><th>ID</th><th>Name</th><th>Location</th><th>Owner ID</th><th>Motors</th><th>Actions</th></tr></thead><tbody>';
                    farms.forEach(farm => {
                        html += `
                            <tr>
                                <td>${farm.id}</td>
                                <td>${farm.name}</td>
                                <td>${farm.location}</td>
                                <td>${farm.owner}</td>
                                <td>${farm.motors.length}</td>
                                <td class="table-actions">
                                    <button onclick="editFarm(${farm.id})" class="btn btn-primary"><i class="fas fa-edit"></i> Edit</button>
                                    <button onclick="deleteFarm(${farm.id})" class="btn btn-danger"><i class="fas fa-trash"></i> Delete</button>
                                    <button onclick="viewFarmDetails(${farm.id})" class="btn btn-primary"><i class="fas fa-info-circle"></i> Details</button>
                                </td>
                            </tr>
                        `;
                    });
                    html += '</tbody></table>';
                    $('#farm-list').html(html);
                },
                error: function(xhr) {
                    $('#farm-list').html(`<p>Error: ${xhr.responseText}</p>`);
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

            // Make sure motor IDs are properly added to the form
            farm.motors.forEach(motor => {
                addMotorInput(motor);
                // Double-check the motor ID is set correctly
                console.log("Added motor with ID:", motor.id);
            });

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
                    $('#farm-data').html(`<p>Error: ${xhr.responseText}</p>`);
                }
            });
        }

        function displayFarmData(data) {
            let html = `
                <h3>${data.name} - ${data.location}</h3>
                <p>Owner ID: ${data.owner || 'Not assigned'}</p>
                <h4>Motors and Valves:</h4>
            `;
            if (data.motors && data.motors.length > 0) {
                data.motors.forEach(motor => {
                    html += `
                        <div class="dashboard-card">
                            <h4>Motor ${motor.id} (${motor.motor_type}) - ${motor.valve_count} valves</h4>
                            <div class="table-actions">
                                <button onclick="editMotor(${motor.id}, ${data.id})" class="btn btn-primary">
                                    <i class="fas fa-edit"></i> Edit
                                </button>
                                <button onclick="deleteMotor(${motor.id}, ${data.id})" class="btn btn-danger">
                                    <i class="fas fa-trash"></i> Delete
                                </button>
                                <button onclick="toggleMotor(${motor.id}, ${motor.is_active})"
                                    class="btn ${motor.is_active ? 'btn-danger' : 'btn-success'}">
                                    <i class="fas fa-power-off"></i> ${motor.is_active ? 'Turn Off' : 'Turn On'}
                                </button>
                            </div>
                    `;
                    if (motor.valves && motor.valves.length > 0) {
                        html += '<div class="mt-2">';
                        motor.valves.forEach(valve => {
                            html += `
                                <div class="flex-between">
                                    <span>${valve.name} (ID: ${valve.id}) - ${valve.is_active ? 'Active' : 'Inactive'}</span>
                                    <button onclick="toggleValve(${valve.id}, ${valve.is_active})"
                                        class="btn ${valve.is_active ? 'btn-danger' : 'btn-success'}">
                                        <i class="fas fa-toggle-${valve.is_active ? 'off' : 'on'}"></i> Toggle
                                    </button>
                                </div>
                            `;
                        });
                        html += '</div>';
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
            const valveElement = $(`#farm-data .flex-between:contains('(ID: ${valveId})')`);
            const valveText = valveElement.find('span').text();
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
            $.ajax({
                url: USER_API_URL,
                type: 'GET',
                dataType: 'json',
                success: function(data) {
                    renderUserTable(data);
                },
                error: function(xhr) {
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
                        <td>${user.first_name || ''} ${user.last_name || ''}</td>
                        <td>${user.role || 'N/A'}</td>
                        <td>${user.is_active ? 'Active' : 'Inactive'}</td>
                        <td class="table-actions">
                            <button onclick="fetchUserDetails(${user.id})" class="btn btn-primary">
                                <i class="fas fa-edit"></i> Edit
                            </button>
                            <button onclick="showDeleteConfirmation(${user.id})" class="btn btn-danger">
                                <i class="fas fa-trash"></i> Delete
                            </button>
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
            $('#phoneNumber').val(user.phone_number || '');
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
                phone_number: $('#phoneNumber').val()
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

        // Add flex-between helper
        document.head.insertAdjacentHTML('beforeend', `
            <style>
                .flex-between {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin: 10px 0;
                }
            </style>
        `);

    function checkUIN(motorIndex, motorId) {
    const uinValue = $(`#UIN-${motorIndex}`).val();

    if (!uinValue) return; // Skip validation if empty

    $.ajax({
        url: `${API_BASE_URL}check-uin/?uin=${uinValue}&exclude=${motorId || ''}`,
        method: 'GET',
        success: function(response) {
            if (response.exists) {
                showNotification(`Warning: UIN ${uinValue} is already in use.`, 'warning');
                $(`#UIN-${motorIndex}`).addClass('error-input');
            } else {
                $(`#UIN-${motorIndex}`).removeClass('error-input');
            }
        }
    });
}