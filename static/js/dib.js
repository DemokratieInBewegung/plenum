function update_notifications(data) {
	// for the django notifications top right.
	// https://github.com/django-notifications/django-notifications#how-to-use
    var menu = document.getElementById(notify_menu_id);
    if (menu) {
        var content = [];
        menu.innerHTML = data.unread_list.map(function (item) {
        	var message = "";
        	switch (item.verb) {
        		case "init_invite":
        			message = `<a href="/initiative/${item.target_object_id}">
        				<i class="material-icons">email</i>${item.actor} hat dich zu "${item.description}" eingeladen
        			</a>`
        			break;
        		default:
		            if(typeof item.actor !== 'undefined'){
		                message = item.actor;
		            }
		            if(typeof item.verb !== 'undefined'){
		                message = message + " " + item.verb;
		            }
		            if(typeof item.target !== 'undefined'){
		                message = message + " " + item.target;
		            }
		            if(typeof item.timestamp !== 'undefined'){
		                message = message + " " + item.timestamp;
		            }
        	}
        	console.log(message);
	        return '<li>' + message + '</li>';
           
        }).join('')
    }
	
}