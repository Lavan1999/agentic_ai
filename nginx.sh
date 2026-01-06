#!/bin/bash

sudo systemctl reload nginx
sudo systemctl restart nginx
sudo supervisorctl restart ai-agent_group:ai-agent
