// Initialise Pusher
const pusher = new Pusher('1032c65dcd261012270a', {
    cluster: 'us2',
    encrypted: true
});

// Subscribe to movie_bot channel
const channel = pusher.subscribe('hotel2');

  // bind new_message event to movie_bot channel
  channel.bind('new_message', function(data) {


   // Append human message
    $('.chat-container').append(`
        <div class="chat-message col-md-5 human-message">
            ${input_message}
        </div>
    `)
    

    // Append bot message
    $('.chat-container').append(`
        <div class="chat-message col-md-5 offset-md-7 bot-message">
        </div>
    `)


});

window.onbeforeunload=function (){
	$.post("/closefile",{message:'closeme',socketId: pusher.connection.socket_id});
}


function submit_message(message) {
	$.ajax({
		url:"/send_message",
		type:"POST",
		data:{message: message, socketId: pusher.connection.socket_id},
		success:handle_response
	});
	
    
    function handle_response(data) {
      // append the bot repsonse to the div
      $('.chat-container').append(`
            <div class="chat-message col-md-5 offset-md-7 bot-message">
                ${data.message}
            </div>
      `)
		 for (var key in data.location)
			 if ("city"== key){
				 getweather(data.location.city)	 
				}
         if (data.message.includes("HOTEL NAME")){

             $('.chat-container').append(`
            <div class = "image offset-md-7">
                <img id='badge' src="static/hotel_reviews/hotel_review.png" alt="User Image"  style="width:300px;height:150px;">
            </div>
         `) 
          document.getElementById("badge").src="static/hotel_reviews/hotel_review.png?_="+new Date().getTime();
}


      // remove the loading indicator
      $( "#loading" ).remove();
    }
}



$('#target').on('submit', function(e){
    e.preventDefault();
    const input_message = $('#input_message').val()
    // return if the user does not enter any text
    if (!input_message) {
      return
    }
    
    $('.chat-container').append(`
        <div class="chat-message col-md-5 human-message">
            ${input_message}
        </div>
    `)
    
    // loading 
    $('.chat-container').append(`
        <div class="chat-message text-center col-md-2 offset-md-10 bot-message" id="loading">
            <b>...</b>
        </div>
    `)
    
    // clear the text input 
    $('#input_message').val('')
 
   
    // send the message
    submit_message(input_message)


    $('.chat-container').animate({
        scrollTop: $('.chat-container').get(0).scrollHeight - $('.bot-message').get(0).scrollHeight
        }, 3000);

});
