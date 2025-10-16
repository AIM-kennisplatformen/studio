import {useState} from "react";
import { Button } from "@/components/ui/button"
export function Chat() {
    const [message, setMessage] = useState('');

    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            const response = await fetch('http://localhost:8000/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({message}),
            });
            const reply = await response.text();
            setMessage(reply);
        } catch (error) {
            console.error('Error sending message:', error);
        }
    };

    const handleInputChange = (e) => {
        setMessage(e.target.value);
    };

    return (
        <div className="p-4">
            <Button>Button</Button>    
            <form onSubmit={handleSubmit} className="flex gap-2">
                <input
                    type="text"
                    value={message}
                    onChange={handleInputChange}
                    placeholder="Type your message..."
                    className="flex-grow p-2 border rounded-lg"
                />
                <button
                    type="submit"
                    className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600"
                >
                    Send
                </button>
            </form>
        </div>
    );
}
