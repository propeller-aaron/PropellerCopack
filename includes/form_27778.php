<?php
	if (empty($_POST['name_5714_9473_27751_16808_19711_8862_17860_27778']) && strlen($_POST['name_5714_9473_27751_16808_19711_8862_17860_27778']) == 0 || empty($_POST['email_5714_9473_27751_16808_19711_8862_17860_27778']) && strlen($_POST['email_5714_9473_27751_16808_19711_8862_17860_27778']) == 0 || empty($_POST['message_5714_9473_27751_16808_19711_8862_17860_27778']) && strlen($_POST['message_5714_9473_27751_16808_19711_8862_17860_27778']) == 0)
	{
		return false;
	}
	
	$name_5714_9473_27751_16808_19711_8862_17860_27778 = $_POST['name_5714_9473_27751_16808_19711_8862_17860_27778'];
	$email_5714_9473_27751_16808_19711_8862_17860_27778 = $_POST['email_5714_9473_27751_16808_19711_8862_17860_27778'];
	$message_5714_9473_27751_16808_19711_8862_17860_27778 = $_POST['message_5714_9473_27751_16808_19711_8862_17860_27778'];
	$optin_5714_9473_27751_16808_19711_8862_17860_27778 = $_POST['optin_5714_9473_27751_16808_19711_8862_17860_27778'];
	
	// Create Message	
	$to = 'mbrown@propellerinc.com';
	$email_subject = "New quote request from Propeller website";
	$email_body = "You have received a new contact form submission from the Propeller website. \n\nName_5714_9473_27751_16808_19711_8862_17860_27778: $name_5714_9473_27751_16808_19711_8862_17860_27778 \nEmail_5714_9473_27751_16808_19711_8862_17860_27778: $email_5714_9473_27751_16808_19711_8862_17860_27778 \nMessage_5714_9473_27751_16808_19711_8862_17860_27778: $message_5714_9473_27751_16808_19711_8862_17860_27778 \nOptin_5714_9473_27751_16808_19711_8862_17860_27778: $optin_5714_9473_27751_16808_19711_8862_17860_27778 \n";
	$headers = "MIME-Version: 1.0\r\nContent-type: text/plain; charset=UTF-8\r\n";	
	$headers .= "From: noreply@propellerinc.com\r\n";
	$headers .= "Reply-To: $email_5714_9473_27751_16808_19711_8862_17860_27778";

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