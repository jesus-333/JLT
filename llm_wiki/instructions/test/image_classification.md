Since you're here... let's implement a simple test for the `autoresearch run`. 

The test should be the training of a neural network , with a dataset created by the combination of `FashionMNIST`, `KMNIST`, `EMNIST` and `CIFAR10` (just to spice up a little bit)

Model is written in `PyTorch`. Dataset downloaded from `torchvision.dataset`.

The config for this experiment are :
- use_cnn_backbone : Boolean. If True add a cnn backbone
- n_cnn_layer : number of cnn layers to add if use_cnn_backbone is True
- cnn_layer_size : list of integers. Size of each cnn layer if use_cnn_backbone is True
- pool_layer_size : list of integers. Size of each pooling layer if use_cnn_backbone is True
- n_fc_layer : number of fully connected layers to add after the cnn backbone
- dropout_2d_rate : float. Dropout rate to use in the cnn layers. If 0, no dropout is applied
- batch_norm_cnn : Boolean. If True, apply batch normalization after each cnn layer
- fc_layer_size : list of integers. Size of each fully connected layer
- activation_function : string. Activation function to use in the fully connected layers. Can be one of ['relu', 'tanh', 'sigmoid', 'leaky_relu', 'elu', 'selu', 'gelu']
- dropout_rate : float. Dropout rate to use in the fully connected layers. If 0, no dropout is applied
- batch_norm_fc : Boolean. If True, apply batch normalization after each fully connected layer
- learning_rate : float. Learning rate to use in the optimizer
- optimizer : string. Optimizer to use. Can be one of ['sgd', 'adam', 'rmsprop', 'adagrad', 'adadelta', 'adamax', 'nadam']
- batch_size : int. Batch size to use in the dataloader
- num_epochs : int. Number of epochs to train the model
- loss_function : string. Loss function to use. Can be one of ['cross_entropy', 'mse', 'mae', 'huber', 'kldiv', 'nll', 'bce', 'bce_with_logits']
- use_scheduler : Boolean. If True, use a learning rate scheduler
- gamma : float. Gamma value to use in the learning rate scheduler if use_scheduler is True
- seed : int. Random seed to use for reproducibility

Each `run` should be executed for at max `num_epochs` epochs or `10` minutes, whichever comes first. 

The metric to optimize is the accuracy on the validation set.
