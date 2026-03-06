import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { getAllCreators, createCollaboration } from "../services/api";
import "./CreateCollaboration.css";

export default function CreateCollaboration(){

const navigate = useNavigate();

const [creators,setCreators] = useState([]);

const [form,setForm] = useState({
creator_id:"",
campaign_name:"",
agreed_price:"",
deadline:"",
status:"pending"
});

useEffect(()=>{
loadCreators();
},[]);


const loadCreators = async()=>{

try{

const res = await getAllCreators();
setCreators(res?.data?.data || []);

}catch(err){
console.error("Creator fetch failed",err);
}

};


const handleChange = (e)=>{

const {name,value} = e.target;

setForm({
...form,
[name]:value
});

};


const handleSubmit = async(e)=>{

e.preventDefault();

try{

const payload = {

creator_id:form.creator_id,
deal_type:"reel",
agreed_price:Number(form.agreed_price),
currency:"INR",
deadline:form.deadline,
status:form.status,
notes:form.campaign_name,
deliverables:["1 reel","1 story"]

};

await createCollaboration(payload);

alert("Collaboration created successfully");

navigate("/collaborations");

}catch(err){

console.error(err);
alert("Failed to create collaboration");

}

};


return(

<div className="create-collab-container">

<div className="create-collab-card">

<h1 className="page-title">
Create Collaboration
</h1>


<form className="collab-form" onSubmit={handleSubmit}>


{/* CREATOR */}

<div className="collab-field">

<label>Select Creator</label>

<select
className="cm-input"
name="creator_id"
value={form.creator_id}
onChange={handleChange}
required
>

<option value="">
Choose creator
</option>

{creators.map((creator)=>(
<option
key={creator.creator_id}
value={creator.creator_id}
>
{creator.username}
</option>
))}

</select>

</div>


{/* GRID */}

<div className="form-grid">

<div className="collab-field">

<label>Campaign Name</label>

<input
className="cm-input"
type="text"
name="campaign_name"
placeholder="Fitness Promotion"
value={form.campaign_name}
onChange={handleChange}
required
/>

</div>


<div className="collab-field">

<label>Agreed Price</label>

<input
className="cm-input"
type="number"
name="agreed_price"
placeholder="₹ Price"
value={form.agreed_price}
onChange={handleChange}
required
/>

</div>


<div className="collab-field">

<label>Deadline</label>

<input
className="cm-input"
type="date"
name="deadline"
value={form.deadline}
onChange={handleChange}
required
/>

</div>


<div className="collab-field">

<label>Status</label>

<select
className="cm-input"
name="status"
value={form.status}
onChange={handleChange}
>

<option value="pending">Pending</option>
<option value="active">Active</option>
<option value="completed">Completed</option>

</select>

</div>

</div>


<button
className="create-btn"
type="submit"
>
Create Collaboration
</button>


</form>

</div>

</div>

);

}