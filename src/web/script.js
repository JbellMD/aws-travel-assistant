// API configuration
const API_CONFIG = {
    // Replace with your actual API Gateway endpoint when deployed
    baseUrl: 'https://api-id.execute-api.region.amazonaws.com/v1',
    endpoints: {
        chat: '/chat',
        ideation: '/ideation',
        availability: '/availability',
        booking: '/booking',
        bookingsQA: '/bookings-qa'
    }
};

// Session management
let sessionId = localStorage.getItem('travelAssistantSessionId') || '';
let userId = localStorage.getItem('travelAssistantUserId') || '';

// DOM elements
document.addEventListener('DOMContentLoaded', () => {
    // Chat elements
    const messagesContainer = document.getElementById('messagesContainer');
    const messageInput = document.getElementById('messageInput');
    const sendButton = document.getElementById('sendButton');
    const typingIndicator = document.getElementById('typingIndicator');
    
    // Ideation elements
    const ideationForm = document.getElementById('ideationForm');
    const ideationLoading = document.getElementById('ideationLoading');
    const ideationResults = document.getElementById('ideationResults');
    const ideaContainer = document.getElementById('ideaContainer');
    
    // Availability elements
    const availabilityForm = document.getElementById('availabilityForm');
    const availabilityType = document.getElementById('availabilityType');
    const flightFields = document.getElementById('flightFields');
    const hotelFields = document.getElementById('hotelFields');
    const activityFields = document.getElementById('activityFields');
    const availabilityLoading = document.getElementById('availabilityLoading');
    const availabilityResults = document.getElementById('availabilityResults');
    const availabilityContainer = document.getElementById('availabilityContainer');
    
    // Booking elements
    const bookingForm = document.getElementById('bookingForm');
    const bookingType = document.getElementById('bookingType');
    const addPassengerBtn = document.getElementById('addPassengerBtn');
    const passengerContainer = document.getElementById('passengerContainer');
    const bookingLoading = document.getElementById('bookingLoading');
    const bookingResults = document.getElementById('bookingResults');
    const bookingContainer = document.getElementById('bookingContainer');
    
    // Bookings Q&A elements
    const bookingsQAForm = document.getElementById('bookingsQAForm');
    const bookingsQALoading = document.getElementById('bookingsQALoading');
    const bookingsQAResults = document.getElementById('bookingsQAResults');
    const bookingsQAContainer = document.getElementById('bookingsQAContainer');
    
    // Initialize event listeners
    initChatListeners();
    initIdeationListeners();
    initAvailabilityListeners();
    initBookingListeners();
    initBookingsQAListeners();
    
    // Initialize userId if not already set
    if (!userId) {
        userId = generateId();
        localStorage.setItem('travelAssistantUserId', userId);
    }
    
    // Chat functionality
    function initChatListeners() {
        // Send message on button click
        sendButton.addEventListener('click', sendMessage);
        
        // Send message on Enter key press
        messageInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                sendMessage();
            }
        });
    }
    
    function sendMessage() {
        const message = messageInput.value.trim();
        if (!message) return;
        
        // Add user message to chat
        addMessageToChat(message, 'user');
        messageInput.value = '';
        
        // Show typing indicator
        showTypingIndicator();
        
        // Send message to API
        callChatAPI(message)
            .then(response => {
                // Hide typing indicator
                hideTypingIndicator();
                
                // Add assistant response to chat
                addMessageToChat(response.message, 'assistant');
                
                // Update session ID if provided
                if (response.session_id) {
                    sessionId = response.session_id;
                    localStorage.setItem('travelAssistantSessionId', sessionId);
                }
                
                // Scroll to bottom
                scrollToBottom();
            })
            .catch(error => {
                console.error('Error sending message:', error);
                hideTypingIndicator();
                addMessageToChat('Sorry, there was an error processing your request. Please try again.', 'assistant');
                scrollToBottom();
            });
        
        // Scroll to bottom
        scrollToBottom();
    }
    
    function addMessageToChat(text, sender) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `${sender}-message message`;
        messageDiv.textContent = text;
        messagesContainer.appendChild(messageDiv);
    }
    
    function showTypingIndicator() {
        typingIndicator.classList.remove('hidden');
    }
    
    function hideTypingIndicator() {
        typingIndicator.classList.add('hidden');
    }
    
    function scrollToBottom() {
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
    
    // Ideation functionality
    function initIdeationListeners() {
        ideationForm.addEventListener('submit', (e) => {
            e.preventDefault();
            
            // Get form values
            const query = document.getElementById('ideaQuery').value.trim();
            const budget = document.getElementById('budget').value.trim();
            const duration = document.getElementById('duration').value.trim();
            
            // Get interests
            const interests = [];
            if (document.getElementById('adventure').checked) interests.push('adventure');
            if (document.getElementById('culture').checked) interests.push('culture');
            if (document.getElementById('culinary').checked) interests.push('culinary');
            if (document.getElementById('relaxation').checked) interests.push('relaxation');
            
            // Validate
            if (!query) {
                alert('Please enter what kind of trip you are looking for.');
                return;
            }
            
            // Show loading
            ideationLoading.classList.remove('hidden');
            
            // Prepare data
            const preferences = {
                budget: budget,
                trip_duration: duration,
                interests: interests
            };
            
            // Call ideation API
            callIdeationAPI(query, preferences)
                .then(response => {
                    // Hide loading
                    ideationLoading.classList.add('hidden');
                    
                    // Display results
                    displayIdeationResults(response.ideas);
                })
                .catch(error => {
                    console.error('Error getting travel ideas:', error);
                    ideationLoading.classList.add('hidden');
                    alert('Sorry, there was an error processing your request. Please try again.');
                });
        });
    }
    
    function displayIdeationResults(ideas) {
        // Clear previous results
        ideaContainer.innerHTML = '';
        
        // Add new results
        ideas.forEach((idea, index) => {
            const ideaCard = document.createElement('div');
            ideaCard.className = 'card mb-3';
            
            const cardBody = document.createElement('div');
            cardBody.className = 'card-body';
            
            const title = document.createElement('h4');
            title.className = 'card-title';
            title.textContent = idea.title;
            
            const description = document.createElement('p');
            description.className = 'card-text';
            description.textContent = idea.description;
            
            const highlightsList = document.createElement('ul');
            highlightsList.className = 'list-group list-group-flush mb-3';
            
            idea.highlights.forEach(highlight => {
                const item = document.createElement('li');
                item.className = 'list-group-item';
                item.textContent = highlight;
                highlightsList.appendChild(item);
            });
            
            const duration = document.createElement('p');
            duration.className = 'card-text';
            duration.innerHTML = `<strong>Ideal Duration:</strong> ${idea.duration}`;
            
            // Append elements
            cardBody.appendChild(title);
            cardBody.appendChild(description);
            cardBody.appendChild(highlightsList);
            cardBody.appendChild(duration);
            ideaCard.appendChild(cardBody);
            
            ideaContainer.appendChild(ideaCard);
        });
        
        // Show results section
        ideationResults.classList.remove('hidden');
    }
    
    // Availability functionality
    function initAvailabilityListeners() {
        // Change form fields based on availability type
        availabilityType.addEventListener('change', function() {
            const type = this.value;
            
            // Hide all field containers
            flightFields.classList.add('hidden');
            hotelFields.classList.add('hidden');
            activityFields.classList.add('hidden');
            
            // Show the selected container
            if (type === 'flight') {
                flightFields.classList.remove('hidden');
            } else if (type === 'hotel') {
                hotelFields.classList.remove('hidden');
            } else if (type === 'activity') {
                activityFields.classList.remove('hidden');
            } else if (type === 'package') {
                flightFields.classList.remove('hidden');
                hotelFields.classList.remove('hidden');
            }
        });
        
        // Form submission
        availabilityForm.addEventListener('submit', (e) => {
            e.preventDefault();
            
            const type = availabilityType.value;
            let searchParams = {};
            
            // Get field values based on type
            if (type === 'flight' || type === 'package') {
                searchParams.origin = document.getElementById('origin').value.trim();
                searchParams.destination = document.getElementById('destination').value.trim();
                searchParams.departure_date = document.getElementById('departureDate').value;
                searchParams.return_date = document.getElementById('returnDate').value;
                searchParams.cabin_class = document.getElementById('cabinClass').value;
                searchParams.passengers = 1;
                
                // Validate
                if (!searchParams.origin || !searchParams.destination || !searchParams.departure_date) {
                    alert('Please fill in all required flight fields.');
                    return;
                }
            }
            
            if (type === 'hotel' || type === 'package') {
                searchParams.location = document.getElementById('location').value.trim();
                searchParams.check_in = document.getElementById('checkIn').value;
                searchParams.check_out = document.getElementById('checkOut').value;
                searchParams.rooms = document.getElementById('rooms').value;
                searchParams.guests = document.getElementById('guests').value;
                
                // Validate hotel fields if this is hotel-only search
                if (type === 'hotel' && (!searchParams.location || !searchParams.check_in || !searchParams.check_out)) {
                    alert('Please fill in all required hotel fields.');
                    return;
                }
            }
            
            if (type === 'activity') {
                searchParams.location = document.getElementById('activityLocation').value.trim();
                searchParams.date = document.getElementById('activityDate').value;
                searchParams.activity_type = document.getElementById('activityType').value;
                searchParams.participants = document.getElementById('participants').value;
                
                // Validate
                if (!searchParams.location || !searchParams.date) {
                    alert('Please fill in all required activity fields.');
                    return;
                }
            }
            
            // Show loading
            availabilityLoading.classList.remove('hidden');
            
            // Call availability API
            callAvailabilityAPI(type, searchParams)
                .then(response => {
                    // Hide loading
                    availabilityLoading.classList.add('hidden');
                    
                    // Display results
                    displayAvailabilityResults(type, response);
                })
                .catch(error => {
                    console.error('Error checking availability:', error);
                    availabilityLoading.classList.add('hidden');
                    alert('Sorry, there was an error processing your request. Please try again.');
                });
        });
    }
    
    function displayAvailabilityResults(type, results) {
        // Clear previous results
        availabilityContainer.innerHTML = '';
        
        // Create type-specific display
        if (type === 'flight') {
            displayFlightResults(results);
        } else if (type === 'hotel') {
            displayHotelResults(results);
        } else if (type === 'activity') {
            displayActivityResults(results);
        } else if (type === 'package') {
            displayPackageResults(results);
        }
        
        // Show results section
        availabilityResults.classList.remove('hidden');
    }
    
    function displayFlightResults(results) {
        const resultsDiv = document.createElement('div');
        
        // Create header
        const header = document.createElement('div');
        header.className = 'alert alert-info';
        header.innerHTML = `<strong>Flight Results:</strong> ${results.outbound_flights.length} flights found from ${results.origin} to ${results.destination}`;
        
        resultsDiv.appendChild(header);
        
        // Create outbound flights section
        const outboundTitle = document.createElement('h4');
        outboundTitle.textContent = 'Outbound Flights';
        resultsDiv.appendChild(outboundTitle);
        
        results.outbound_flights.forEach(flight => {
            const flightCard = createFlightCard(flight, 'outbound');
            resultsDiv.appendChild(flightCard);
        });
        
        // Create return flights section if available
        if (results.return_flights && results.return_flights.length > 0) {
            const returnTitle = document.createElement('h4');
            returnTitle.className = 'mt-4';
            returnTitle.textContent = 'Return Flights';
            resultsDiv.appendChild(returnTitle);
            
            results.return_flights.forEach(flight => {
                const flightCard = createFlightCard(flight, 'return');
                resultsDiv.appendChild(flightCard);
            });
        }
        
        availabilityContainer.appendChild(resultsDiv);
    }
    
    function createFlightCard(flight, direction) {
        const card = document.createElement('div');
        card.className = 'card mb-3';
        
        const cardBody = document.createElement('div');
        cardBody.className = 'card-body';
        
        // Parse dates
        const departureTime = new Date(flight.departure_time);
        const arrivalTime = new Date(flight.arrival_time);
        
        // Create content
        cardBody.innerHTML = `
            <div class="row">
                <div class="col-md-8">
                    <h5>${flight.airline} - Flight ${flight.flight_number}</h5>
                    <div class="d-flex justify-content-between">
                        <div>
                            <strong>${departureTime.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</strong>
                            <div>${flight.origin}</div>
                        </div>
                        <div class="text-center">
                            <div><i class="fas fa-plane ${direction === 'return' ? 'fa-flip-horizontal' : ''}"></i></div>
                            <div>${Math.floor(flight.duration_minutes / 60)}h ${flight.duration_minutes % 60}m</div>
                        </div>
                        <div>
                            <strong>${arrivalTime.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</strong>
                            <div>${flight.destination}</div>
                        </div>
                    </div>
                    <div class="mt-2">
                        <span class="badge bg-info">${flight.cabin}</span>
                        <span class="badge bg-secondary">${flight.available_seats} seats available</span>
                    </div>
                </div>
                <div class="col-md-4 text-end">
                    <div class="fs-4 mb-2">$${flight.price}</div>
                    <button class="btn btn-sm btn-primary select-flight" 
                            data-flight-id="${flight.airline}-${flight.flight_number}-${departureTime.toISOString().split('T')[0]}-${flight.cabin}">
                        Select
                    </button>
                </div>
            </div>
        `;
        
        card.appendChild(cardBody);
        return card;
    }
    
    // Booking functionality
    function initBookingListeners() {
        // Add passenger button
        addPassengerBtn.addEventListener('click', addPassengerFields);
        
        // Booking form submission
        bookingForm.addEventListener('submit', (e) => {
            e.preventDefault();
            
            // Get booking type
            const type = bookingType.value;
            
            // Get booking details based on type
            let details = {};
            let userInfo = {};
            let paymentInfo = {};
            
            // Get common user info
            userInfo = {
                id: userId,
                name: document.getElementById('contactName').value.trim(),
                email: document.getElementById('contactEmail').value.trim(),
                phone: document.getElementById('contactPhone').value.trim()
            };
            
            // Get payment info (in a real app, this would be handled securely)
            paymentInfo = {
                card_number: document.getElementById('paymentCardNumber').value.trim().replace(/\D/g, ''),
                expiration: document.getElementById('paymentExpiration').value.trim(),
                cvv: document.getElementById('paymentCvv').value.trim(),
                name: document.getElementById('paymentName').value.trim()
            };
            
            // Validate common fields
            if (!userInfo.name || !userInfo.email || !userInfo.phone) {
                alert('Please fill in all contact information fields.');
                return;
            }
            
            if (!paymentInfo.card_number || !paymentInfo.expiration || !paymentInfo.cvv || !paymentInfo.name) {
                alert('Please fill in all payment information fields.');
                return;
            }
            
            // Get type-specific details
            if (type === 'flight') {
                details.flight_id = document.getElementById('flightId').value.trim();
                details.passengers = getPassengerInfo();
                
                // Validate
                if (!details.flight_id) {
                    alert('Please enter a flight ID.');
                    return;
                }
                
                if (details.passengers.length === 0) {
                    alert('Please add at least one passenger.');
                    return;
                }
            }
            
            // Show loading
            bookingLoading.classList.remove('hidden');
            
            // Call booking API
            callBookingAPI(type, details, userInfo, paymentInfo)
                .then(response => {
                    // Hide loading
                    bookingLoading.classList.add('hidden');
                    
                    // Display results
                    displayBookingResults(type, response);
                })
                .catch(error => {
                    console.error('Error processing booking:', error);
                    bookingLoading.classList.add('hidden');
                    alert('Sorry, there was an error processing your booking. Please try again.');
                });
        });
    }
    
    function addPassengerFields() {
        const passengerDiv = document.createElement('div');
        passengerDiv.className = 'passenger-info mb-3 p-2 border rounded';
        
        passengerDiv.innerHTML = `
            <div class="row">
                <div class="col-md-6">
                    <input type="text" class="form-control mb-2" placeholder="First Name">
                </div>
                <div class="col-md-6">
                    <input type="text" class="form-control mb-2" placeholder="Last Name">
                </div>
            </div>
            <div class="row">
                <div class="col-md-6">
                    <input type="date" class="form-control mb-2" placeholder="Date of Birth">
                </div>
                <div class="col-md-6">
                    <input type="text" class="form-control mb-2" placeholder="Passport Number">
                </div>
            </div>
            <button type="button" class="btn btn-sm btn-danger remove-passenger">Remove</button>
        `;
        
        // Add remove button functionality
        passengerDiv.querySelector('.remove-passenger').addEventListener('click', function() {
            passengerContainer.removeChild(passengerDiv);
        });
        
        passengerContainer.appendChild(passengerDiv);
    }
    
    function getPassengerInfo() {
        const passengers = [];
        const passengerDivs = passengerContainer.querySelectorAll('.passenger-info');
        
        passengerDivs.forEach(div => {
            const inputs = div.querySelectorAll('input');
            
            const passenger = {
                first_name: inputs[0].value.trim(),
                last_name: inputs[1].value.trim(),
                date_of_birth: inputs[2].value,
                passport: inputs[3].value.trim(),
                name: `${inputs[0].value.trim()} ${inputs[1].value.trim()}`
            };
            
            // Only add if at least name is provided
            if (passenger.first_name && passenger.last_name) {
                passengers.push(passenger);
            }
        });
        
        return passengers;
    }
    
    function displayBookingResults(type, results) {
        // Clear previous results
        bookingContainer.innerHTML = '';
        
        // Create booking confirmation
        const confirmationDiv = document.createElement('div');
        confirmationDiv.className = 'alert alert-success';
        confirmationDiv.innerHTML = `
            <h4><i class="fas fa-check-circle me-2"></i>Booking Confirmed!</h4>
            <p>Your confirmation code: <strong>${results.confirmation.confirmation_code}</strong></p>
            <p>Booking ID: ${results.booking_id}</p>
            <p>Status: ${results.status}</p>
        `;
        
        bookingContainer.appendChild(confirmationDiv);
        
        // Create booking details card
        const detailsCard = document.createElement('div');
        detailsCard.className = 'card';
        
        const cardHeader = document.createElement('div');
        cardHeader.className = 'card-header';
        cardHeader.innerHTML = `<h5>Booking Details</h5>`;
        
        const cardBody = document.createElement('div');
        cardBody.className = 'card-body';
        
        // Add type-specific details
        if (type === 'flight') {
            const flight = results.confirmation;
            cardBody.innerHTML = `
                <p><strong>Airline:</strong> ${flight.airline}</p>
                <p><strong>Flight:</strong> ${flight.flight_number}</p>
                <p><strong>Date:</strong> ${flight.departure_date}</p>
                <p><strong>Class:</strong> ${flight.cabin_class}</p>
                <p><strong>Passengers:</strong> ${flight.passenger_count}</p>
                <div><strong>Passenger Names:</strong></div>
                <ul>
                    ${flight.passenger_names.map(name => `<li>${name}</li>`).join('')}
                </ul>
                <p><strong>Total Price:</strong> $${flight.total_amount}</p>
            `;
        }
        
        detailsCard.appendChild(cardHeader);
        detailsCard.appendChild(cardBody);
        
        bookingContainer.appendChild(detailsCard);
        
        // Show results section
        bookingResults.classList.remove('hidden');
    }
    
    // Bookings Q&A functionality
    function initBookingsQAListeners() {
        bookingsQAForm.addEventListener('submit', (e) => {
            e.preventDefault();
            
            // Get form values
            const query = document.getElementById('bookingQuery').value.trim();
            const userIdInput = document.getElementById('userId').value.trim();
            
            // Validate
            if (!query) {
                alert('Please enter your question.');
                return;
            }
            
            if (!userIdInput) {
                alert('Please enter your user ID.');
                return;
            }
            
            // Show loading
            bookingsQALoading.classList.remove('hidden');
            
            // Call bookings Q&A API
            callBookingsQAAPI(query, userIdInput)
                .then(response => {
                    // Hide loading
                    bookingsQALoading.classList.add('hidden');
                    
                    // Display results
                    displayBookingsQAResults(response);
                })
                .catch(error => {
                    console.error('Error getting answer:', error);
                    bookingsQALoading.classList.add('hidden');
                    alert('Sorry, there was an error processing your request. Please try again.');
                });
        });
    }
    
    function displayBookingsQAResults(response) {
        // Clear previous results
        bookingsQAContainer.innerHTML = '';
        
        // Create answer card
        const answerCard = document.createElement('div');
        answerCard.className = 'card';
        
        const cardBody = document.createElement('div');
        cardBody.className = 'card-body';
        
        // Add question
        const questionDiv = document.createElement('div');
        questionDiv.className = 'alert alert-secondary';
        questionDiv.textContent = response.query;
        
        // Add answer
        const answerDiv = document.createElement('div');
        answerDiv.className = 'mt-3';
        answerDiv.textContent = response.answer;
        
        // Add to card
        cardBody.appendChild(questionDiv);
        cardBody.appendChild(answerDiv);
        answerCard.appendChild(cardBody);
        
        bookingsQAContainer.appendChild(answerCard);
        
        // Show results section
        bookingsQAResults.classList.remove('hidden');
    }
    
    // API calls
    async function callChatAPI(message) {
        const response = await fetch(`${API_CONFIG.baseUrl}${API_CONFIG.endpoints.chat}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message: message,
                session_id: sessionId,
                user_id: userId
            })
        });
        
        if (!response.ok) {
            throw new Error(`API error: ${response.status}`);
        }
        
        return await response.json();
    }
    
    async function callIdeationAPI(query, preferences) {
        const response = await fetch(`${API_CONFIG.baseUrl}${API_CONFIG.endpoints.ideation}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                query: query,
                preferences: preferences,
                context: {
                    user_id: userId
                }
            })
        });
        
        if (!response.ok) {
            throw new Error(`API error: ${response.status}`);
        }
        
        return await response.json();
    }
    
    async function callAvailabilityAPI(type, params) {
        const response = await fetch(`${API_CONFIG.baseUrl}${API_CONFIG.endpoints.availability}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                type: type,
                params: params,
                user_id: userId
            })
        });
        
        if (!response.ok) {
            throw new Error(`API error: ${response.status}`);
        }
        
        return await response.json();
    }
    
    async function callBookingAPI(type, details, user_info, payment_info) {
        const response = await fetch(`${API_CONFIG.baseUrl}${API_CONFIG.endpoints.booking}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                type: type,
                details: details,
                user_info: user_info,
                payment_info: payment_info
            })
        });
        
        if (!response.ok) {
            throw new Error(`API error: ${response.status}`);
        }
        
        return await response.json();
    }
    
    async function callBookingsQAAPI(query, user_id) {
        const response = await fetch(`${API_CONFIG.baseUrl}${API_CONFIG.endpoints.bookingsQA}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                query: query,
                user_id: user_id
            })
        });
        
        if (!response.ok) {
            throw new Error(`API error: ${response.status}`);
        }
        
        return await response.json();
    }
    
    // Utility functions
    function generateId() {
        return 'user_' + Math.random().toString(36).substring(2, 15);
    }
});
