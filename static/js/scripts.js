
const API_BASE_URL = 'http://127.0.0.1:8000/farm/';
const USER_API_URL = 'http://127.0.0.1:8000/users/';
const ITEMS_PER_PAGE = 10;

$(document).ready(function() {
    const token = localStorage.getItem('adminToken');
    if (!token) {
        window.location.href = '/';
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
    fetchUsers(1);

    // Farm List events
    $('#refreshFarmBtn').click(() => fetchFarms(1));
    $('#farmSearch').on('input', debounce(() => fetchFarms(1), 300));
    $('#farmPrevBtn').click(() => fetchFarms(currentFarmPage - 1));
    $('#farmNextBtn').click(() => fetchFarms(currentFarmPage + 1));

    // User List events
    $('#addUserBtn').click(() => {
        resetUserForm();
        showSection('create-user');
    });
    $('#userSearch').on('input', debounce(() => fetchUsers(1), 300));
    $('#userPrevBtn').click(() => fetchUsers(currentUserPage - 1));
    $('#userNextBtn').click(() => fetchUsers(currentUserPage + 1));

    // Initialize active section
    showSection('dashboard');
});

// Debounce function to prevent excessive API calls during search
function debounce(func, wait) {
    let timeout;
    return function(...args) {
        clearTimeout(timeout);
        timeout = setTimeout(() => func.apply(this, args), wait);
    };
}

function toggleDrawer() {
    const drawer = document.getElementById('drawer');
    const content = document.getElementById('content');
    drawer.classList.toggle('open');
    content.classList.toggle('shifted');
}

function logout() {
    localStorage.removeItem('adminToken');
    window.location.replace('/');
}

function showSection(sectionId) {
    $('.section').removeClass('active');
    $('.nav-btn').removeClass('active');
    $(`#${sectionId}-section`).addClass('active');
    $(`#${sectionId}-btn`).addClass('active');

    switch(sectionId) {
        case 'farm-list':
            fetchFarms(1);
            break;
        case 'dashboard':
            loadDashboardData();
            break;
        case 'user-list':
            fetchUsers(1);
            break;
    }
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
            ownerSelect.empty().append('<option value="">Select Owner</option>');

            // Check if users is an array or has a results property (paginated)
            let userList = Array.isArray(users) ? users : (users.results || []);

            if (!userList || userList.length === 0) {
                $('#owner-error').text('No users found');
                return;
            }

            userList.forEach(user => {
                ownerSelect.append(`<option value="${user.id}">${user.email} (${user.role || 'user'})</option>`);
            });

            $('#owner-error').text('');
        },
        error: function(xhr) {
            $('#owner-error').text(`Failed to load owners: ${xhr.statusText}`);
            console.error('Error loading owners:', xhr);
        }
    });
}

let motorCount = 0;

function addMotorInput(motor = null) {
    motorCount++;
    const motorHtml = `
        <div class="motor-input flex gap-4 mb-4" id="motor-${motorCount}">
            <input type="number" id="UIN-${motorCount}" value="${motor?.UIN || ''}"
                   placeholder="UIN" class="flex-1" onblur="checkUIN(${motorCount}, '${motor?.id || ''}')">
            <input type="hidden" id="motor-id-${motorCount}" value="${motor?.id || ''}">
            <select id="motor-type-${motorCount}" class="flex-1">
                <option value="single_phase" ${motor?.motor_type === 'single_phase' ? 'selected' : ''}>Single Phase</option>
                <option value="double_phase" ${motor?.motor_type === 'double_phase' ? 'selected' : ''}>Double Phase</option>
                <option value="triple_phase" ${motor?.motor_type === 'triple_phase' ? 'selected' : ''}>Triple Phase</option>
            </select>
            <input type="number" id="valve-count-${motorCount}"
                   placeholder="Valve Count" min="1" value="${motor?.valve_count || ''}" class="flex-1">
            <button type="button" onclick="$(this).closest('.motor-input').remove()"
                    class="btn-danger">Remove</button>
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
            // Handle potential paginated response
            const motorList = Array.isArray(motors) ? motors : (motors.results || []);

            const existingMotor = motorList.find(motor => motor.UIN == uinValue && motor.id != currentMotorId);
            if (existingMotor) {
                showNotification(`UIN ${uinValue} is already taken by Motor ID: ${existingMotor.id}`, 'error');
                uinInput.val('');
            }
        },
        error: function(xhr) {
            showNotification(`Error checking UIN: ${xhr.statusText}`, 'error');
            console.error('Error checking UIN:', xhr);
        }
    });
}

function saveFarm() {
    const farmId = $('#farm-edit-id').val();
    const motors = [];
    let hasError = false;

    $('.motor-input').each(function() {
        const motorId = $(this).find('[id^="motor-id-"]').val();
        const motorUIN = $(this).find('[id^="UIN-"]').val();
        const motorType = $(this).find('[id^="motor-type-"]').val();
        const valveCount = parseInt($(this).find('[id^="valve-count-"]').val()) || 0;

        if (valveCount < 1) {
            showNotification('Valve count must be at least 1', 'error');
            hasError = true;
            return false;
        }

        const motorObject = {
            motor_type: motorType,
            valve_count: valveCount,
            UIN: motorUIN || null
        };
        if (motorId) motorObject.id = motorId;
        motors.push(motorObject);
    });

    if (hasError || motors.length === 0) {
        if (!hasError) showNotification('Please add at least one motor', 'error');
        return;
    }

    const farmData = {
        name: $('#farm-name').val().trim() || 'Unnamed Farm',
        location: $('#farm-location').val().trim() || 'Unknown Location',
        owner: parseInt($('#farm-owner').val()) || null,
        motors: motors
    };

    $.ajax({
        url: farmId ? `${API_BASE_URL}farms/${farmId}/` : `${API_BASE_URL}farms/`,
        method: farmId ? 'PUT' : 'POST',
        contentType: 'application/json',
        data: JSON.stringify(farmData),
        success: function(response) {
            showNotification(`Farm ${farmId ? 'updated' : 'created'} successfully`);
            resetFarmForm();
            showSection('farm-list');
        },
        error: function(xhr) {
            const error = xhr.responseJSON || {};
            let message = 'Error saving farm: ';
            if (error.motors) {
                message += error.motors.map((m, i) => `Motor ${i+1}: ${m.UIN?.[0] || 'Invalid data'}`).join('; ');
            } else {
                message += xhr.statusText;
            }
            showNotification(message, 'error');
            console.error('Error saving farm:', xhr);
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

let currentFarmPage = 1;
let totalFarmPages = 1;

function fetchFarms(page) {
    currentFarmPage = page < 1 ? 1 : page;
    const searchQuery = $('#farmSearch').val().trim();
    $("#farm-loading").show();
    $("#farmTable").empty();

    // Construct URL with query parameters for search and pagination
    let url = `${API_BASE_URL}farms/`;
    const queryParams = new URLSearchParams();

    if (searchQuery) {
        queryParams.append('search', searchQuery);
    }

    queryParams.append('page', currentFarmPage);
    queryParams.append('limit', ITEMS_PER_PAGE);

    if (queryParams.toString()) {
        url += `?${queryParams.toString()}`;
    }

    $.ajax({
        url: url,
        method: 'GET',
        success: function(response) {
            $("#farm-loading").hide();
            let farms = [];

            // Handle paginated response
            if (response && response.results !== undefined) {
                farms = response.results;
                totalFarmPages = Math.ceil(response.count / ITEMS_PER_PAGE);
            }
            // Handle array response
            else if (Array.isArray(response)) {
                // For search filtering when backend doesn't support it
                if (searchQuery) {
                    response = response.filter(farm =>
                        farm.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                        farm.location.toLowerCase().includes(searchQuery.toLowerCase())
                    );
                }

                const totalItems = response.length;
                totalFarmPages = Math.ceil(totalItems / ITEMS_PER_PAGE);

                // Apply manual pagination
                const startIndex = (currentFarmPage - 1) * ITEMS_PER_PAGE;
                const endIndex = startIndex + ITEMS_PER_PAGE;
                farms = response.slice(startIndex, endIndex);
            }
            // Handle unexpected response
            else {
                console.error("Unexpected response format:", response);
                showNotification("Received unexpected data format from server", "error");
                farms = [];
                totalFarmPages = 1;
            }

            if (farms.length === 0) {
                $("#farmTable").html("<tr><td colspan='6' class='text-center'>No farms found</td></tr>");
            } else {
                farms.forEach(farm => {
                    $("#farmTable").append(`
                        <tr>
                            <td>${farm.id || 'N/A'}</td>
                            <td>${farm.name || 'Unnamed'}</td>
                            <td>${farm.location || 'Unknown'}</td>
                            <td>${farm.owner_name || farm.owner || 'Not assigned'}</td>
                            <td>${farm.motors ? farm.motors.length : 0}</td>
                            <td>
                                <button onclick="editFarm(${farm.id})" class="btn-primary">Edit</button>
                                <button onclick="deleteFarm(${farm.id})" class="btn-danger">Delete</button>
                                <button onclick="viewFarmDetails(${farm.id})" class="btn-primary">View</button>
                            </td>
                        </tr>
                    `);
                });
            }

            // Update pagination controls
            updateFarmPagination();
        },
        error: function(xhr, status, error) {
            $("#farm-loading").hide();
            $("#farmTable").html(`<tr><td colspan='6' class='text-danger text-center'>Error: ${xhr.statusText || 'Failed to load farms'}</td></tr>`);
            console.error('Fetch farms error:', xhr, status, error);
        }
    });
}

function updateFarmPagination() {
    $('#farmPageInfo').text(`Page ${currentFarmPage} of ${totalFarmPages}`);
    $('#farmPrevBtn').prop('disabled', currentFarmPage <= 1);
    $('#farmNextBtn').prop('disabled', currentFarmPage >= totalFarmPages);
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

            // Check if motors is array or undefined
            const motors = farm.motors || [];
            if (motors.length > 0) {
                motors.forEach(motor => addMotorInput(motor));
            } else {
                addMotorInput(); // Add one empty motor input
            }

            showSection('create-farm');
        },
        error: function(xhr) {
            showNotification('Error loading farm: ' + (xhr.responseJSON?.detail || xhr.statusText), 'error');
            console.error('Error loading farm:', xhr);
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
                fetchFarms(currentFarmPage);
                loadDashboardData(); // Refresh dashboard counts
            },
            error: function(xhr) {
                showNotification('Error deleting farm: ' + (xhr.responseJSON?.detail || xhr.statusText), 'error');
                console.error('Error deleting farm:', xhr);
            }
        });
    }
}

function viewFarmDetails(farmId) {
    $('#farm-id').val(farmId);
    getFarmData();
    showSection('farm-details');
}

function getFarmData() {
    const farmId = $('#farm-id').val();
    if (!farmId) {
        $('#farm-data').html('<p class="text-danger">Please enter a Farm ID</p>');
        return;
    }
    $.ajax({
        url: `${API_BASE_URL}farms/${farmId}/`,
        method: 'GET',
        success: function(data) {
            displayFarmData(data);
        },
        error: function(xhr) {
            $('#farm-data').html(`<p class="text-danger">Error: ${xhr.responseJSON?.detail || xhr.statusText}</p>`);
            console.error('Error fetching farm data:', xhr);
        }
    });
}

function loadDashboardData() {
    $.ajax({
        url: `${API_BASE_URL}farms/`,
        method: 'GET',
        success: function(response) {
            let farms = [];

            // Handle both paginated and array responses
            if (response && response.results !== undefined) {
                farms = response.results;
                $('#total-farms').text(response.count || 0);
            } else if (Array.isArray(response)) {
                farms = response;
                $('#total-farms').text(farms.length);
            } else {
                $('#total-farms').text(0);
                return;
            }

            let totalMotors = 0;
            let totalValves = 0;

            farms.forEach(farm => {
                if (farm.motors && Array.isArray(farm.motors)) {
                    totalMotors += farm.motors.length;

                    farm.motors.forEach(motor => {
                        if (motor.valves && Array.isArray(motor.valves)) {
                            totalValves += motor.valves.length;
                        } else if (motor.valve_count) {
                            totalValves += motor.valve_count;
                        }
                    });
                }
            });

            $('#total-motors').text(totalMotors);
            $('#total-valves').text(totalValves);

            // Display recent farms (e.g., the first 3 farms)
            displayRecentFarms(farms.slice(0, 3));
        },
        error: function(xhr) {
            showNotification('Error loading farm data: ' + (xhr.responseJSON?.detail || xhr.statusText), 'error');
            console.error('Error loading dashboard data:', xhr);
            $('#total-farms').text('Error');
            $('#total-motors').text('Error');
            $('#total-valves').text('Error');
            $('#recent-farms').html('<p class="text-danger">Error loading recent farms</p>');
        }
    });

    $.ajax({
        url: USER_API_URL,
        method: 'GET',
        success: function(response) {
            // Handle both paginated and array responses
            if (response && response.results !== undefined) {
                $('#total-users').text(response.count || 0);
            } else if (Array.isArray(response)) {
                $('#total-users').text(response.length);
            } else {
                $('#total-users').text(0);
            }
        },
        error: function(xhr) {
            showNotification('Error loading user data: ' + (xhr.responseJSON?.detail || xhr.statusText), 'error');
            console.error('Error loading user data:', xhr);
            $('#total-users').text('Error');
        }
    });
}

function displayRecentFarms(farms) {
    const recentFarmsContainer = $('#recent-farms-container');
    recentFarmsContainer.empty();

    if (!farms || farms.length === 0) {
        recentFarmsContainer.html('<p class="text-center text-gray-500">No farms available</p>');
        return;
    }

    farms.forEach(farm => {
        const motorCount = farm.motors ? farm.motors.length : 0;
        const valveCount = farm.motors ? farm.motors.reduce((sum, motor) => sum + (motor.valve_count || 0), 0) : 0;

        recentFarmsContainer.append(`
            <div class="bg-white p-4 rounded-lg shadow">
                <h4 class="font-medium text-gray-800">${farm.name || 'Unnamed Farm'}</h4>
                <p class="text-sm text-gray-600">Location: ${farm.location || 'Unknown'}</p>
                <p class="text-sm text-gray-600">Owner: ${farm.owner_name || farm.owner || 'Not assigned'}</p>
                <p class="text-sm text-gray-600">Motors: ${motorCount}</p>
                <p class="text-sm text-gray-600">Valves: ${valveCount}</p>
            </div>
        `);
    });
}

function displayFarmData(data) {
    let html = `
        <h3 class="text-lg font-semibold mb-2">${data.name || 'Unnamed Farm'} - ${data.location || 'Unknown Location'}</h3>
        <p class="text-sm text-gray-600 mb-4">Owner: ${data.owner_name || data.owner || 'Not assigned'}</p>
        <h4 class="text-md font-semibold mt-4 mb-2">Motors and Valves:</h4>
    `;

    if (data.motors && Array.isArray(data.motors) && data.motors.length > 0) {
        data.motors.forEach(motor => {
            html += `
                <div class="p-4 bg-white rounded-lg shadow mt-4">
                    <h4 class="text-md font-medium text-gray-800 mb-2">
                        Motor ${motor.id} (${motor.motor_type || 'Unknown type'}) - ${motor.valve_count || 0} valves -
                        Status: <span class="${motor.is_active ? 'text-green-600' : 'text-red-600'}">${motor.is_active ? 'On' : 'Off'}</span>
                    </h4>
                    <div class="flex flex-wrap gap-3">
                        <button onclick="editMotor(${motor.id}, ${data.id})" class="btn-primary text-sm py-1 px-3 fixed-width-btn">Edit</button>
                        <button onclick="deleteMotor(${motor.id}, ${data.id})" class="btn-danger text-sm py-1 px-3 fixed-width-btn">Delete</button>
                        <button onclick="toggleMotor(${motor.id}, ${motor.is_active ? 1 : 0})"
                                class="toggle-motor-btn ${motor.is_active ? 'btn-active' : 'btn-inactive'} text-sm py-1 px-3 fixed-width-btn"
                                data-motor-id="${motor.id}">
                            ${motor.is_active ? 'Turn Off' : 'Turn On'}
                        </button>
                    </div>
            `;

            if (motor.valves && Array.isArray(motor.valves) && motor.valves.length > 0) {
                html += `<div class="mt-3">`;
                motor.valves.forEach(valve => {
                    html += `
                        <div class="flex items-center justify-between gap-3 mt-2 py-2 border-t border-gray-200">
                            <span class="text-sm text-gray-600 flex-1 truncate">
                                ${valve.name || `Valve ${valve.id}`} (ID: ${valve.id}) -
                                Status: <span class="${valve.is_active ? 'text-green-600' : 'text-red-600'}">${valve.is_active ? 'Active' : 'Inactive'}</span>
                            </span>
                            <button onclick="toggleValve(${valve.id}, ${valve.is_active ? 1 : 0})"
                                    class="toggle-valve-btn ${valve.is_active ? 'btn-active' : 'btn-inactive'} text-sm py-1 px-3 fixed-width-btn"
                                    data-valve-id="${valve.id}">
                                Toggle
                            </button>
                        </div>
                    `;
                });
                html += `</div>`;
            } else {
                html += `<p class="text-sm text-gray-600 mt-2">No valves assigned yet</p>`;
            }
            html += `</div>`;
        });
    } else {
        html += `<p class="text-sm text-gray-600">No motors assigned to this farm</p>`;
    }
    $('#farm-data').html(html);
}

function toggleMotor(motorId, currentStatus) {
    const newStatus = currentStatus ? 0 : 1;
    const $button = $(`.toggle-motor-btn[data-motor-id="${motorId}"]`);

    $.ajax({
        url: `${API_BASE_URL}motors/${motorId}/`,
        method: 'PATCH',
        contentType: 'application/json',
        data: JSON.stringify({ is_active: newStatus }),
        success: function() {
            showNotification(`Motor ${motorId} ${newStatus ? 'activated' : 'deactivated'} successfully`);
            // Update button text and class
            $button.text(newStatus ? 'Turn Off' : 'Turn On');
            $button.removeClass(newStatus ? 'btn-inactive' : 'btn-active');
            $button.addClass(newStatus ? 'btn-active' : 'btn-inactive');
            getFarmData(); // Refresh farm data
        },
        error: function(xhr) {
            showNotification('Error toggling motor: ' + (xhr.responseJSON?.detail || xhr.statusText), 'error');
            console.error('Error toggling motor:', xhr);
        }
    });
}

function toggleValve(valveId, currentStatus) {
    const newStatus = currentStatus ? 0 : 1;
    const $button = $(`.toggle-valve-btn[data-valve-id="${valveId}"]`);
    const valveElement = $(`.valve:contains("(ID: ${valveId}")`);
    let valveName = `Valve ${valveId}`;

    if (valveElement.length > 0) {
        const valveText = valveElement.text();
        const valveNameMatch = valveText.match(/^(.*?)\s*\(ID:/);
        if (valveNameMatch && valveNameMatch[1]) {
            valveName = valveNameMatch[1].trim();
        }
    }

    $.ajax({
        url: `${API_BASE_URL}valves/${valveId}/`,
        method: 'PATCH',
        contentType: 'application/json',
        data: JSON.stringify({
            name: valveName,
            is_active: newStatus
        }),
        success: function() {
            showNotification(`Valve ${valveId} ${newStatus ? 'activated' : 'deactivated'} successfully`);
            // Update button class
            $button.removeClass(newStatus ? 'btn-inactive' : 'btn-active');
            $button.addClass(newStatus ? 'btn-active' : 'btn-inactive');
            getFarmData(); // Refresh farm data
        },
        error: function(xhr) {
            showNotification('Error toggling valve: ' + (xhr.responseJSON?.detail || xhr.statusText), 'error');
            console.error('Error toggling valve:', xhr);
        }
    });
}


function editMotor(motorId, farmId) {
    $.ajax({
        url: `${API_BASE_URL}motors/${motorId}/`,
        method: 'GET',
        success: function(motor) {
            editFarm(farmId);
            // Use setTimeout to ensure the farm edit form is populated first
            setTimeout(() => {
                for (let i = 1; i <= motorCount; i++) {
                    if ($(`#motor-id-${i}`).val() == motorId) {
                        $(`#UIN-${i}`).val(motor.UIN);
                        $(`#motor-type-${i}`).val(motor.motor_type);
                        $(`#valve-count-${i}`).val(motor.valve_count);
                        break;
                    }
                }
            }, 300); // Increased timeout to ensure farm edit form is loaded
        },
        error: function(xhr) {
            showNotification('Error loading motor: ' + (xhr.responseJSON?.detail || xhr.statusText), 'error');
            console.error('Error loading motor:', xhr);
        }
    });
}

function deleteMotor(motorId, farmId) {
    if (confirm('Are you sure you want to delete this motor?')) {
        $.ajax({
            url: `${API_BASE_URL}motors/${motorId}/`,
            method: 'DELETE',
            success: function() {
                showNotification('Motor deleted successfully');
                getFarmData(); // Refresh farm details
                if ($('#farm-edit-id').val() == farmId) {
                    editFarm(farmId); // Refresh farm edit form if open
                }
            },
            error: function(xhr) {
                showNotification('Error deleting motor: ' + (xhr.responseJSON?.detail || xhr.statusText), 'error');
                console.error('Error deleting motor:', xhr);
            }
        });
    }
}

function loadDashboardData() {
    $.ajax({
        url: `${API_BASE_URL}farms/`,
        method: 'GET',
        success: function(response) {
            let farms = [];

            // Handle both paginated and array responses
            if (response && response.results !== undefined) {
                farms = response.results;
                $('#total-farms').text(response.count || 0);
            } else if (Array.isArray(response)) {
                farms = response;
                $('#total-farms').text(farms.length);
            } else {
                $('#total-farms').text(0);
                return;
            }

            let totalMotors = 0;
            let totalValves = 0;

            farms.forEach(farm => {
                if (farm.motors && Array.isArray(farm.motors)) {
                    totalMotors += farm.motors.length;

                    farm.motors.forEach(motor => {
                        if (motor.valves && Array.isArray(motor.valves)) {
                            totalValves += motor.valves.length;
                        } else if (motor.valve_count) {
                            totalValves += motor.valve_count;
                        }
                    });
                }
            });

            $('#total-motors').text(totalMotors);
            $('#total-valves').text(totalValves);

            // Display recent farms (e.g., the first 3 farms)
            displayRecentFarms(farms.slice(0, 3));
        },
        error: function(xhr) {
            showNotification('Error loading farm data: ' + (xhr.responseJSON?.detail || xhr.statusText), 'error');
            console.error('Error loading dashboard data:', xhr);
            $('#total-farms').text('Error');
            $('#total-motors').text('Error');
            $('#total-valves').text('Error');
            $('#recent-farms').html('<p class="text-danger">Error loading recent farms</p>');
        }
    });

    $.ajax({
        url: USER_API_URL,
        method: 'GET',
        success: function(response) {
            // Handle both paginated and array responses
            if (response && response.results !== undefined) {
                $('#total-users').text(response.count || 0);
            } else if (Array.isArray(response)) {
                $('#total-users').text(response.length);
            } else {
                $('#total-users').text(0);
            }
        },
        error: function(xhr) {
            showNotification('Error loading user data: ' + (xhr.responseJSON?.detail || xhr.statusText), 'error');
            console.error('Error loading user data:', xhr);
            $('#total-users').text('Error');
        }
    });
}

// User Management Functions
let currentUserPage = 1;
let totalUserPages = 1;

function fetchUsers(page) {
    currentUserPage = page < 1 ? 1 : page;
    const searchQuery = $('#userSearch').val().trim();
    $('#user-loading').show();
    $('#userTable').empty();

    // Construct URL with query parameters
    let url = USER_API_URL;
    const queryParams = new URLSearchParams();

    if (searchQuery) {
        queryParams.append('search', searchQuery);
    }

    queryParams.append('page', currentUserPage);
    queryParams.append('limit', ITEMS_PER_PAGE);

    if (queryParams.toString()) {
        url += `?${queryParams.toString()}`;
    }

    $.ajax({
        url: url,
        type: 'GET',
        success: function(response) {
            $('#user-loading').hide();
            let users = [];

            // Handle paginated response
            if (response && response.results !== undefined) {
                users = response.results;
                totalUserPages = Math.ceil(response.count / ITEMS_PER_PAGE);
            }
            // Handle array response
            else if (Array.isArray(response)) {
                // For search filtering when backend doesn't support it
                if (searchQuery) {
                    response = response.filter(user =>
                        (user.username && user.username.toLowerCase().includes(searchQuery.toLowerCase())) ||
                        (user.email && user.email.toLowerCase().includes(searchQuery.toLowerCase())) ||
                        (user.first_name && user.first_name.toLowerCase().includes(searchQuery.toLowerCase())) ||
                        (user.last_name && user.last_name.toLowerCase().includes(searchQuery.toLowerCase()))
                    );
                }

                const totalItems = response.length;
                totalUserPages = Math.ceil(totalItems / ITEMS_PER_PAGE);

                // Apply manual pagination
                const startIndex = (currentUserPage - 1) * ITEMS_PER_PAGE;
                const endIndex = startIndex + ITEMS_PER_PAGE;
                users = response.slice(startIndex, endIndex);
            }
            // Handle unexpected response
            else {
                console.error("Unexpected response format:", response);
                showNotification("Received unexpected data format from server", "error");
                users = [];
                totalUserPages = 1;
            }

            if (!users || users.length === 0) {
                $('#userTable').html("<tr><td colspan='8' class='text-center'>No users found</td></tr>");
            } else {
                users.forEach(user => {
                    $('#userTable').append(`
                        <tr>
                            <td>${user.id}</td>
                            <td>${user.username || 'N/A'}</td>
                            <td>${user.email || 'N/A'}</td>
                            <td>${user.first_name || ''}</td>
                            <td>${user.last_name || ''}</td>
                            <td>${user.role || 'user'}</td>
                            <td>${user.is_active ? 'Active' : 'Inactive'}</td>
                            <td>
                                <button onclick="fetchUserDetails(${user.id})" class="btn-primary">Edit</button>
                                <button onclick="showDeleteConfirmation(${user.id})" class="btn-danger">Delete</button>
                            </td>
                        </tr>
                    `);
                });
            }
            updateUserPagination();
        },
        error: function(xhr, status, error) {
            $('#user-loading').hide();
            $('#userTable').html(`<tr><td colspan='8' class='text-danger text-center'>Error: ${xhr.statusText || 'Failed to load users'}</td></tr>`);
            console.error('Fetch users error:', xhr, status, error);
        }
    });
}

function updateUserPagination() {
    $('#userPageInfo').text(`Page ${currentUserPage} of ${totalUserPages}`);
    $('#userPrevBtn').prop('disabled', currentUserPage <= 1);
    $('#userNextBtn').prop('disabled', currentUserPage >= totalUserPages);
}

function fetchUserDetails(userId) {
    $.ajax({
        url: `${USER_API_URL}${userId}/`,
        type: 'GET',
        success: function(user) {
            populateUserForm(user);
            currentUserId = user.id;
            $('#userFormTitle').text('Edit User');
            $('#passwordHint').removeClass('hidden');
            showSection('create-user');
        },
        error: function(xhr) {
            showNotification('Failed to load user details: ' + (xhr.responseJSON?.detail || xhr.statusText), 'error');
            console.error('Error loading user details:', xhr);
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
            fetchUsers(currentUserPage);
        },
        error: function(xhr) {
            showNotification('Failed to create user: ' + xhr.statusText, 'error');
            console.error('Error creating user:', xhr);
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
            fetchUsers(currentUserPage);
        },
        error: function(xhr) {
            showNotification('Failed to update user: ' + xhr.statusText, 'error');
            console.error('Error updating user:', xhr);
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
            fetchUsers(currentUserPage);
        },
        error: function(xhr) {
            showNotification('Failed to delete user: ' + xhr.statusText, 'error');
            console.error('Error deleting user:', xhr);
        }
    });
}

function gatherUserFormData() {
    const password = $('#password').val();
    const confirmPassword = $('#confirmPassword').val();

    if (password && password !== confirmPassword) {
        showNotification('Passwords do not match', 'error');
        return null;
    }

    const userData = {
        username: $('#username').val().trim(),
        email: $('#email').val().trim(),
        first_name: $('#firstName').val().trim(),
        last_name: $('#lastName').val().trim(),
        role: $('#role').val(),
        is_active: $('#isActive').is(':checked'),
        phone_number: $('#phoneNumber').val().trim(),
        address: $('#address').val().trim()
    };

    if (password) userData.password = password;
    return userData;
}

function resetUserForm() {
    $('#userForm')[0].reset();
    $('#userId').val('');
    currentUserId = null;
    $('#userFormTitle').text('Create New User');
    $('#passwordHint').addClass('hidden');
}

let currentUserId = null;

$('#saveUserBtn').click(function() {
    const userData = gatherUserFormData();
    if (!userData) return;

    if (currentUserId) {
        updateUser(currentUserId, userData);
    } else {
        createUser(userData);
    }
});