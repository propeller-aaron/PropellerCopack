<?php
	if (empty($_POST['name_5714_9473_27751_16808_48569']) && strlen($_POST['name_5714_9473_27751_16808_48569']) == 0 || empty($_POST['email_5714_9473_27751_16808_48569']) && strlen($_POST['email_5714_9473_27751_16808_48569']) == 0 || empty($_POST['message_5714_9473_27751_16808_48569']) && strlen($_POST['message_5714_9473_27751_16808_48569']) == 0)
	{
		return false;
	}
	
	$name_5714_9473_27751_16808_48569 = $_POST['name_5714_9473_27751_16808_48569'];
	$email_5714_9473_27751_16808_48569 = $_POST['email_5714_9473_27751_16808_48569'];
	$message_5714_9473_27751_16808_48569 = $_POST['message_5714_9473_27751_16808_48569'];
	$optin_5714_9473_27751_16808_48569 = $_POST['optin_5714_9473_27751_16808_48569'];
	
	// Create Message	
	$to = 'mbrown@propellerinc.com';
	$email_subject = "New quote request from Propeller website";
	$email_body = "You have received a new contact form submission from the Propeller website. \n\nName_5714_9473_27751_16808_48569: $name_5714_9473_27751_16808_48569 \nEmail_5714_9473_27751_16808_48569: $email_5714_9473_27751_16808_48569 \nMessage_5714_9473_27751_16808_48569: $message_5714_9473_27751_16808_48569 \nOptin_5714_9473_27751_16808_48569: $optin_5714_9473_27751_16808_48569 \n";
	$headers = "MIME-Version: 1.0\r\nContent-type: text/plain; charset=UTF-8\r\n";	
	$headers .= "From: noreply@propellerinc.com\r\n";
	$headers .= "Reply-To: $email_5714_9473_27751_16808_48569";

	// Post Message
	if (function_exists('mail'))
	{
		$result = mail($to,$email_subject,$email_body,$headers);
	}
	else // Mail() Disabled
	{
		$error = array("message" => "The php mail() function is not available on this server.");
	    header('Content-Type: application/json');
	    http_response_code(500);
	    echo json_encode($error);
	}	
?>