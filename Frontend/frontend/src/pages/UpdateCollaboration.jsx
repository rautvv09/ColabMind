import React, { useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { updateCollaboration } from "../services/api";

export default function UpdateCollaboration(){

const { id } = useParams();
const navigate = useNavigate();

const [form,setForm] = useState({
status:"",
payment_status:""
});

const handleSubmit = async(e)=>{

e.preventDefault();

try{

await updateCollaboration(id,form);

alert("Updated successfully");

navigate(-1);

}catch(err){

console.error(err);

}

};

return(

<div className="create-collab-container">

<div className="cm-card create-collab-card">

<h1 className="page-title">
Update Collaboration
</h1>

<form onSubmit={handleSubmit} className="collab-form">

<div className="collab-field">

<label>Status</label>

<select
className="cm-input"
onChange={(e)=>setForm({...form,status:e.target.value})}
>

<option value="">Select</option>
<option value="pending">Pending</option>
<option value="active">Active</option>
<option value="completed">Completed</option>
<option value="cancelled">Cancelled</option>

</select>

</div>

<div className="collab-field">

<label>Payment Status</label>

<select
className="cm-input"
onChange={(e)=>setForm({...form,payment_status:e.target.value})}
>

<option value="">Select</option>
<option value="paid">Paid</option>
<option value="unpaid">Unpaid</option>

</select>

</div>

<button className="btn-cm create-btn">

Update Collaboration

</button>

</form>

</div>

</div>

);

}