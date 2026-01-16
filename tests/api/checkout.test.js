const request = require('supertest');
const express = require('express');
const CheckoutAPI = require('../apps/license-backend/api/checkout'); // Adjust the path as per your structure

const app = express();
app.use(express.json());
app.use('/api/checkout', new CheckoutAPI(/* dependencies */).router);

describe('Checkout API', () => {
    it('should create a checkout session', async () => {
        const response = await request(app)
            .post('/api/checkout/create-session')
            .send({ plan: 'monthly', success_url: 'http://success.com', cancel_url: 'http://cancel.com' });
        
        expect(response.status).toBe(200);
        expect(response.body).toHaveProperty('session_id');
    });

    it('should handle validation errors', async () => {
        const response = await request(app)
            .post('/api/checkout/create-session')
            .send({}); // Invalid body

        expect(response.status).toBe(400);
        expect(response.body).toHaveProperty('error');
    });

    // Add more tests for success and cancel endpoints
});