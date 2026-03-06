import React, { useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { updateCollaboration } from "../services/api";

export default function UpdateCollaboration(){

const { id } = useParams();
const navigate = useNavigate();

const [form,setForm] = useState({
deal_type:"",
agreed_price:""
});

const handleSubmit = async(e)=>{

e.preventDefault();

try{

const payload = {
deal_type:form.deal_type,
agreed_price:Number(form.agreed_price)
};

await updateCollaboration(id,payload);

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

<label>Deal Type</label>

<select
className="cm-input"
onChange={(e)=>setForm({...form,deal_type:e.target.value})}
>

<option value="">Select</option>
<option value="reel">Reel</option>
<option value="story">Story</option>

</select>

</div>

<div className="collab-field">

<label>Price Change / Update</label>

<input
className="cm-input"
type="number"
placeholder="Enter price"
onChange={(e)=>setForm({...form,agreed_price:e.target.value})}
/>

</div>

<button className="btn-cm create-btn">

Update Collaboration

</button>

</form>

</div>

</div>

);

}